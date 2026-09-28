"""Realtime status assembly from stored heartbeats."""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlmodel import Session, select

from heartbeat.protocol.models import ONLINE_TIMEOUT_MS
from heartbeat.server.config import get_settings
from heartbeat.server.models import Heartbeat
from heartbeat.server.schemas import (
    ClientStatus,
    MediaPayload,
    PrivacyPayload,
    ProcessPayload,
    ScreenshotStatus,
    StatusPayload,
    SystemPayload,
)
from heartbeat.server.services.snapshots import SnapshotStore
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)


class StatusService:
    """Build the realtime status payload for a client."""

    _instance: StatusService | None = None

    @classmethod
    def instance(cls) -> StatusService:
        """Return the process-wide status service singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def resolve_client_id(self, session: Session, requested: str | None) -> str:
        """Pick the client id from request, settings, or latest heartbeat."""
        settings = get_settings()
        for candidate in (requested, settings.default_client_id):
            if candidate:
                return candidate
        return self._latest_client_id(session)

    def build(self, session: Session, client_id: str) -> StatusPayload:
        """Assemble status for client_id using the newest heartbeat and snapshot."""
        row = self._latest_heartbeat(session, client_id)
        if row is None:
            return StatusPayload(online=False)
        payload = json.loads(row.payload_json or "{}")
        now_ms = current_ms()
        timeout_ms = get_settings().online_timeout_ms or ONLINE_TIMEOUT_MS
        online = (now_ms - row.ts) < timeout_ms
        snapshot = SnapshotStore.instance().read_latest(client_id)
        privacy = _privacy_status(payload.get("privacy") or {})
        show_screenshot = privacy.screenshot if privacy is not None else False
        return StatusPayload(
            online=online,
            last_heartbeat_ts=row.ts,
            client=_client_status(payload.get("client") or {}),
            system=_system_status(payload.get("system")),
            media=_media_status(payload.get("media")),
            processes=_process_status(payload.get("processes") or []),
            screenshot=_screenshot_status(snapshot if show_screenshot else None),
            privacy=privacy,
        )

    def latest_payload(self, session: Session, client_id: str) -> dict[str, Any]:
        """Return the raw stored heartbeat payload or an empty dict."""
        row = self._latest_heartbeat(session, client_id)
        if row is None:
            return {}
        return json.loads(row.payload_json or "{}")

    def _latest_heartbeat(self, session: Session, client_id: str) -> Heartbeat | None:
        statement = (
            select(Heartbeat).where(Heartbeat.client_id == client_id).order_by(Heartbeat.ts.desc())
        )
        return session.exec(statement).first()

    def _latest_client_id(self, session: Session) -> str:
        statement = select(Heartbeat).order_by(Heartbeat.ts.desc())
        row = session.exec(statement).first()
        return row.client_id if row else ""


def _client_status(raw: dict[str, Any]) -> ClientStatus | None:
    """Build the client status block from stored JSON."""
    if not raw:
        return None
    return ClientStatus(
        id=str(raw.get("id", "")),
        platform=str(raw.get("platform", "")),
        version=str(raw.get("version", "")),
    )


def _system_status(raw: Any) -> SystemPayload | None:
    """Build the system status block from stored JSON."""
    if not raw:
        return None
    return SystemPayload.model_validate(raw)


def _media_status(raw: Any) -> MediaPayload | None:
    """Build the media status block from stored JSON."""
    if not raw:
        return None
    return MediaPayload.model_validate(raw)


def _process_status(raw: Any) -> list[ProcessPayload]:
    """Build the process status list from stored JSON."""
    if not raw:
        return []
    return [ProcessPayload.model_validate(item) for item in raw]


def _screenshot_status(snapshot: Any) -> ScreenshotStatus | None:
    """Build the screenshot status block from snapshot metadata."""
    if snapshot is None:
        return None
    return ScreenshotStatus(
        url=snapshot.url,
        ts=snapshot.ts,
        width=snapshot.width,
        height=snapshot.height,
    )


def _privacy_status(raw: dict[str, Any]) -> PrivacyPayload | None:
    """Build the privacy status block from stored JSON."""
    if not raw:
        return None
    return PrivacyPayload.model_validate(raw)
