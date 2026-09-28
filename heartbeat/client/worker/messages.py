"""Background worker polling guestbook messages and running admin operations."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from heartbeat.client.api import ApiError, ApiService, ApiSettings

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 8_000
FETCH_LIMIT = 50


class MessageWorker(QObject):
    """Poll the guestbook list and run message admin calls off the UI thread."""

    messages_loaded = Signal(object)
    messages_failed = Signal(str)
    message_arrived = Signal(object)
    message_deleted = Signal(int)
    message_delete_failed = Signal(str)
    bans_loaded = Signal(object)
    bans_failed = Signal(str)
    ban_created = Signal(object)
    ban_create_failed = Signal(str)
    ban_deleted = Signal(int)
    ban_delete_failed = Signal(str)

    def __init__(self, service: ApiService, interval_ms: int = POLL_INTERVAL_MS) -> None:
        super().__init__()
        self._service = service
        self._seen_ids: set[int] = set()
        self._primed = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._interval_ms = interval_ms

    @Slot()
    def start(self) -> None:
        """Begin polling and fetch the current page immediately."""
        self._timer.start(self._interval_ms)
        self._poll(report_errors=False)
        logger.info("Message worker started")

    @Slot()
    def stop(self) -> None:
        """Stop the polling timer."""
        self._timer.stop()
        logger.info("Message worker stopped")

    @Slot()
    def refresh(self) -> None:
        """Fetch the message list on demand, reporting failures to the UI."""
        self._poll(report_errors=True)

    @Slot()
    def load_bans(self) -> None:
        """Fetch the IP ban list and emit the result."""
        try:
            data = self._service.list_message_bans()
        except ApiError as exc:
            logger.warning("Ban list load failed: %s", exc.message)
            self.bans_failed.emit(exc.message)
            return
        self.bans_loaded.emit(data)

    @Slot(int)
    def delete_message(self, message_id: int) -> None:
        """Delete one guestbook message and report the outcome."""
        try:
            self._service.delete_message(message_id)
        except ApiError as exc:
            logger.warning("Message delete failed: id=%s %s", message_id, exc.message)
            self.message_delete_failed.emit(exc.message)
            return
        logger.info("Message deleted: id=%s", message_id)
        self.message_deleted.emit(message_id)

    @Slot(str)
    def create_ban(self, ip: str) -> None:
        """Ban a guestbook IP and report the outcome."""
        try:
            data = self._service.create_message_ban(ip)
        except ApiError as exc:
            logger.warning("Ban create failed: ip=%s %s", ip, exc.message)
            self.ban_create_failed.emit(exc.message)
            return
        logger.info("Guestbook IP banned: %s", ip)
        self.ban_created.emit(data)

    @Slot(int)
    def delete_ban(self, ban_id: int) -> None:
        """Remove one guestbook IP ban and report the outcome."""
        try:
            self._service.delete_message_ban(ban_id)
        except ApiError as exc:
            logger.warning("Ban delete failed: id=%s %s", ban_id, exc.message)
            self.ban_delete_failed.emit(exc.message)
            return
        logger.info("Guestbook IP unbanned: id=%s", ban_id)
        self.ban_deleted.emit(ban_id)

    @Slot(object)
    def apply_settings(self, settings: ApiSettings) -> None:
        """Replace the API service after connection settings change."""
        self._service = ApiService.from_settings(settings)
        logger.info("Message worker settings updated")

    @Slot()
    def _on_tick(self) -> None:
        self._poll(report_errors=False)

    def _poll(self, report_errors: bool) -> None:
        try:
            data = self._service.list_messages(limit=FETCH_LIMIT)
        except ApiError as exc:
            logger.warning("Message poll failed: %s", exc.message)
            if report_errors:
                self.messages_failed.emit(exc.message)
            return
        rows = _rows(data)
        self.messages_loaded.emit(data)
        for row in _new_rows(rows, self._seen_ids, self._primed):
            self.message_arrived.emit(row)
        self._primed = True
        self._seen_ids.update(int(row["id"]) for row in rows if isinstance(row.get("id"), int))


def _rows(data: object) -> list[dict[str, Any]]:
    """Extract the message row list from a list payload."""
    payload = data if isinstance(data, dict) else {}
    items = payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _new_rows(
    rows: list[dict[str, Any]],
    seen_ids: set[int],
    primed: bool,
) -> list[dict[str, Any]]:
    """Return unseen rows in chronological order, silent before the first primed poll."""
    if not primed:
        return []
    fresh = [
        row for row in rows if isinstance(row.get("id"), int) and int(row["id"]) not in seen_ids
    ]
    fresh.sort(key=lambda row: int(row.get("created_ts") or 0))
    return fresh
