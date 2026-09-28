from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QMetaObject, QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

from heartbeat.client.api import ApiService, ApiSettings
from heartbeat.client.autostart.base import create_provider
from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.store import ConfigStore, SecretStore
from heartbeat.client.i18n import Translator
from heartbeat.client.notify import show_notification
from heartbeat.client.window.main_window import MainWindow
from heartbeat.client.window.setup_wizard import SetupWizard
from heartbeat.client.worker.api import ApiWorker
from heartbeat.client.worker.messages import MessageWorker

logger = logging.getLogger(__name__)

PAGE_DIARIES = 2
PAGE_FRIENDS = 3
PAGE_MESSAGES = 4


class WindowManager(QObject):
    """Own the main window, API worker thread, and setup wizard lifecycle."""

    config_saved = Signal(object, str, str, str)
    api_settings_changed = Signal(object)
    language_changed = Signal(str)

    _instance: WindowManager | None = None

    def __init__(
        self,
        config_store: ConfigStore,
        secret_store: SecretStore,
        launch_command: str,
    ) -> None:
        super().__init__()
        self._config_store = config_store
        self._secret_store = secret_store
        self._launch_command = launch_command
        self._config = config_store.load()
        self._translator = Translator(self._config.ui.language)
        self._window = MainWindow(self._translator)
        self._api_worker = ApiWorker(
            ApiService(
                self._config.server.base_url,
                self._secret_store.load_api_key(),
                self._config.server.timeout_seconds,
            )
        )
        self._message_worker = MessageWorker(
            ApiService(
                self._config.server.base_url,
                self._secret_store.load_api_key(),
                self._config.server.timeout_seconds,
            )
        )
        self._api_thread = QThread()
        self._api_worker.moveToThread(self._api_thread)
        self._message_worker.moveToThread(self._api_thread)
        self._api_thread.started.connect(self._message_worker.start)
        self._api_thread.start()
        self._wire_window()
        self._wire_api()
        self.api_settings_changed.connect(self._api_worker.apply_settings)
        self.api_settings_changed.connect(self._message_worker.apply_settings)

    @classmethod
    def instance(cls) -> WindowManager:
        """Return the process-wide window manager instance."""
        if cls._instance is None:
            raise RuntimeError("WindowManager is not initialized")
        return cls._instance

    @classmethod
    def initialize(
        cls,
        config_store: ConfigStore,
        secret_store: SecretStore,
        launch_command: str,
    ) -> WindowManager:
        """Create and register the process-wide window manager instance."""
        manager = cls(config_store, secret_store, launch_command)
        cls._instance = manager
        return manager

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def main_window(self) -> MainWindow:
        return self._window

    def api_key(self) -> str:
        """Return the stored api key."""
        return self._secret_store.load_api_key()

    @Slot()
    def show_settings(self) -> None:
        """Show the main window with current values."""
        self._window.apply_config(
            self._config,
            self._secret_store.load_api_key(),
            self._secret_store.load_github_token(),
            self._secret_store.load_github_login(),
        )
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    @Slot()
    def hide_settings(self) -> None:
        """Hide the main window without destroying it."""
        self._window.hide()

    @Slot()
    def toggle_settings(self) -> None:
        """Show the main window when hidden, hide it otherwise."""
        if self._window.is_visible():
            self.hide_settings()
            return
        self.show_settings()

    @Slot()
    def show_setup_wizard(self) -> None:
        """Open the first-run setup wizard modally."""
        wizard = SetupWizard(
            self._translator,
            self._config.server.base_url,
            self._secret_store.load_api_key(),
        )
        wizard.setup_finished.connect(self._on_setup_finished)
        wizard.exec()

    @Slot(object, str, str, str)
    def _on_save(
        self,
        config: AppConfig,
        api_key: str,
        github_token: str,
        github_login: str,
    ) -> None:
        self._config = config
        self._config_store.save(config)
        self._secret_store.save_api_key(api_key)
        self._secret_store.save_github_token(github_token)
        self._secret_store.save_github_login(github_login)
        self._sync_autostart()
        self.config_saved.emit(config, api_key, github_token, github_login)
        self.api_settings_changed.emit(self._api_settings(api_key))
        self._push_github_token(github_token, github_login)
        logger.info("Settings saved")

    @Slot()
    def _on_close(self) -> None:
        self.hide_settings()

    @Slot(str)
    def _on_language(self, language: str) -> None:
        self._config.ui.language = language
        self._config_store.save(self._config)
        self._window.set_language(language)
        self.config_saved.emit(
            self._config,
            self._secret_store.load_api_key(),
            self._secret_store.load_github_token(),
            self._secret_store.load_github_login(),
        )
        self.language_changed.emit(language)
        logger.info("UI language changed: %s", language)

    def _push_github_token(self, token: str, login: str) -> None:
        """Upload the GitHub PAT to the server after a successful local save."""
        if not token:
            return
        try:
            service = ApiService.from_settings(self._api_settings(self._secret_store.load_api_key()))
            service.set_github_token(token, login)
            logger.info("GitHub token pushed to server")
        except Exception:
            logger.exception("GitHub token push failed")

    @Slot(str, str)
    def _on_setup_finished(self, base_url: str, api_key: str) -> None:
        self._config.server.base_url = base_url
        self._config.setup_completed = True
        self._config_store.save(self._config)
        self._secret_store.save_api_key(api_key)
        self._window.apply_config(
            self._config,
            api_key,
            self._secret_store.load_github_token(),
            self._secret_store.load_github_login(),
        )
        self.config_saved.emit(
            self._config,
            api_key,
            self._secret_store.load_github_token(),
            self._secret_store.load_github_login(),
        )
        self.api_settings_changed.emit(self._api_settings(api_key))
        logger.info("Setup wizard completed")

    @Slot(int)
    def _on_page_changed(self, index: int) -> None:
        loaders: dict[int, Callable[[], None]] = {
            PAGE_DIARIES: self._window.diary.load_requested.emit,
            PAGE_FRIENDS: self._window.friends.load_requested.emit,
            PAGE_MESSAGES: self._window.messages.load_requested.emit,
        }
        loader = loaders.get(index)
        if loader is not None:
            loader()

    def _api_settings(self, api_key: str) -> ApiSettings:
        return ApiSettings(
            base_url=self._config.server.base_url,
            api_key=api_key,
            timeout_seconds=self._config.server.timeout_seconds,
        )

    def _wire_window(self) -> None:
        self._window.save_requested.connect(self._on_save)
        self._window.close_requested.connect(self._on_close)
        self._window.language_change_requested.connect(self._on_language)
        self._window.page_changed.connect(self._on_page_changed)
        self._window.display_list_changed.connect(self._on_display_list)
        self._window.background_requested.connect(self._on_background_upload)
        self._window.diagnostics.set_display_list(self._config.process_whitelist)

    @Slot()
    def _on_background_upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self._window,
            self._translator.tr("settings.upload_background"),
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return
        data, content_type = _read_image(path)
        if data is None:
            QMessageBox.warning(self._window, self._translator.tr("app.title"), "Unreadable image")
            return
        try:
            service = ApiService.from_settings(self._api_settings(self._secret_store.load_api_key()))
            service.upload_background(data, content_type)
            QMessageBox.information(self._window, self._translator.tr("app.title"), "Background updated")
            logger.info("Background uploaded: %s", path)
        except Exception:
            logger.exception("Background upload failed")
            QMessageBox.warning(self._window, self._translator.tr("app.title"), "Background upload failed")

    @Slot(list)
    def _on_display_list(self, names: list) -> None:
        cleaned = [str(item).strip() for item in names if str(item).strip()]
        self._config.process_whitelist = list(dict.fromkeys(cleaned))
        self._config_store.save(self._config)
        self.config_saved.emit(
            self._config,
            self._secret_store.load_api_key(),
            self._secret_store.load_github_token(),
            self._secret_store.load_github_login(),
        )
        logger.info("Process display list updated: %s", self._config.process_whitelist)

    def _wire_api(self) -> None:
        diary = self._window.diary
        friends = self._window.friends
        diary.load_requested.connect(self._api_worker.load_diaries)
        diary.create_requested.connect(self._api_worker.create_diary)
        diary.update_requested.connect(self._api_worker.update_diary)
        diary.delete_requested.connect(self._api_worker.delete_diary)
        self._api_worker.diaries_loaded.connect(diary.apply_diaries)
        self._api_worker.diaries_failed.connect(diary.show_error)
        self._api_worker.diary_written.connect(diary.apply_diary_saved)
        self._api_worker.diary_write_failed.connect(diary.show_error)
        self._api_worker.diary_deleted.connect(diary.apply_diary_deleted)
        self._api_worker.diary_delete_failed.connect(diary.show_error)
        friends.load_requested.connect(self._api_worker.load_friends)
        friends.create_requested.connect(self._api_worker.create_friend)
        friends.update_requested.connect(self._api_worker.update_friend)
        friends.delete_requested.connect(self._api_worker.delete_friend)
        self._api_worker.friends_loaded.connect(friends.apply_friends)
        self._api_worker.friends_failed.connect(friends.show_error)
        self._api_worker.friend_written.connect(friends.apply_friend_saved)
        self._api_worker.friend_write_failed.connect(friends.show_error)
        self._api_worker.friend_deleted.connect(friends.apply_friend_deleted)
        self._api_worker.friend_delete_failed.connect(friends.show_error)
        messages = self._window.messages
        messages.load_requested.connect(self._message_worker.refresh)
        self._message_worker.messages_loaded.connect(messages.apply_messages)
        self._message_worker.messages_failed.connect(messages.show_error)
        self._message_worker.message_arrived.connect(self._on_message_arrived)

    @Slot(object)
    def _on_message_arrived(self, row: object) -> None:
        """Show a system notification for a newly arrived guestbook message."""
        payload = row if isinstance(row, dict) else {}
        raw_author = str(payload.get("author") or "").strip()
        author = raw_author or self._translator.tr("message.anonymous")
        content = str(payload.get("content") or "")
        show_notification(self._translator.tr("message.notify_title"), f"{author}: {content}")

    def _sync_autostart(self) -> None:
        provider = create_provider(self._launch_command)
        if self._config.autostart.enabled:
            provider.enable()
            return
        provider.disable()

    def shutdown(self) -> None:
        """Stop the API worker thread before application exit."""
        if self._api_thread.isRunning():
            QMetaObject.invokeMethod(
                self._message_worker, "stop", Qt.ConnectionType.BlockingQueuedConnection
            )
        self._api_thread.quit()
        self._api_thread.wait(3000)


def _read_image(path: str) -> tuple[bytes | None, str]:
    from pathlib import Path

    suffix = Path(path).suffix.lower()
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    content_type = mapping.get(suffix)
    if content_type is None:
        return None, ""
    try:
        return Path(path).read_bytes(), content_type
    except OSError:
        logger.exception("Background image read failed")
        return None, ""
