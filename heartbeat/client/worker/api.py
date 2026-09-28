"""Background worker for diary and friend HTTP operations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QObject, Signal, Slot

from heartbeat.client.api import ApiError, ApiService, ApiSettings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ApiWorker(QObject):
    """Run diary and friend API calls off the UI thread."""

    diaries_loaded = Signal(object)
    diaries_failed = Signal(str)
    diary_written = Signal(object)
    diary_write_failed = Signal(str)
    diary_deleted = Signal(int)
    diary_delete_failed = Signal(str)
    friends_loaded = Signal(object)
    friends_failed = Signal(str)
    friend_written = Signal(object)
    friend_write_failed = Signal(str)
    friend_deleted = Signal(int)
    friend_delete_failed = Signal(str)

    def __init__(self, service: ApiService) -> None:
        super().__init__()
        self._service = service

    @Slot(object)
    def apply_settings(self, settings: ApiSettings) -> None:
        """Replace the API service after connection settings change."""
        self._service = ApiService.from_settings(settings)
        logger.info("API worker settings updated")

    @Slot()
    def load_diaries(self) -> None:
        """Fetch the diary list and emit the result."""
        data, error = self._call(self._service.list_diaries)
        if error:
            self.diaries_failed.emit(error)
            return
        self.diaries_loaded.emit(data)

    @Slot(object)
    def create_diary(self, payload: dict[str, Any]) -> None:
        """Create a diary entry and emit the created row."""
        data, error = self._call(lambda: self._service.create_diary(payload))
        if error:
            self.diary_write_failed.emit(error)
            return
        self.diary_written.emit(data)

    @Slot(int, object)
    def update_diary(self, diary_id: int, payload: dict[str, Any]) -> None:
        """Patch a diary entry and emit the updated row."""
        data, error = self._call(lambda: self._service.update_diary(diary_id, payload))
        if error:
            self.diary_write_failed.emit(error)
            return
        self.diary_written.emit(data)

    @Slot(int)
    def delete_diary(self, diary_id: int) -> None:
        """Delete a diary entry and emit its id."""
        _, error = self._call(lambda: self._service.delete_diary(diary_id))
        if error:
            self.diary_delete_failed.emit(error)
            return
        self.diary_deleted.emit(diary_id)

    @Slot()
    def load_friends(self) -> None:
        """Fetch friend links and emit the result."""
        data, error = self._call(self._service.list_friends)
        if error:
            self.friends_failed.emit(error)
            return
        self.friends_loaded.emit(data)

    @Slot(object)
    def create_friend(self, payload: dict[str, Any]) -> None:
        """Create a friend link and emit the created row."""
        data, error = self._call(lambda: self._service.create_friend(payload))
        if error:
            self.friend_write_failed.emit(error)
            return
        self.friend_written.emit(data)

    @Slot(int, object)
    def update_friend(self, friend_id: int, payload: dict[str, Any]) -> None:
        """Patch a friend link and emit the updated row."""
        data, error = self._call(lambda: self._service.update_friend(friend_id, payload))
        if error:
            self.friend_write_failed.emit(error)
            return
        self.friend_written.emit(data)

    @Slot(int)
    def delete_friend(self, friend_id: int) -> None:
        """Delete a friend link and emit its id."""
        _, error = self._call(lambda: self._service.delete_friend(friend_id))
        if error:
            self.friend_delete_failed.emit(error)
            return
        self.friend_deleted.emit(friend_id)

    def _call(self, action: Callable[[], T]) -> tuple[T | None, str]:
        try:
            return action(), ""
        except ApiError as exc:
            logger.warning("API call failed: %s", exc.message)
            return None, exc.message
