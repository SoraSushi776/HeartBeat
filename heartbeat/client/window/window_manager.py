from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

from heartbeat.client.autostart.base import create_provider
from heartbeat.client.config.models import AppConfig
from heartbeat.client.config.store import ConfigStore, SecretStore
from heartbeat.client.window.settings_view import SettingsView

logger = logging.getLogger(__name__)


class WindowManager(QObject):
    """Own the settings window lifecycle and persist form changes."""

    config_saved = Signal(object, str)

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
        self._view = SettingsView()
        self._view.save_requested.connect(self._on_save)
        self._view.close_requested.connect(self._on_close)

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

    def api_key(self) -> str:
        """Return the stored api key."""
        return self._secret_store.load_api_key()

    @Slot()
    def show_settings(self) -> None:
        """Show the settings window with current values."""
        self._view.apply_config(self._config, self._secret_store.load_api_key())
        self._view.show()
        self._view.raise_()
        self._view.activateWindow()

    @Slot()
    def hide_settings(self) -> None:
        """Hide the settings window without destroying it."""
        self._view.hide()

    @Slot()
    def toggle_settings(self) -> None:
        """Show the settings window when hidden, hide it otherwise."""
        if self._view.is_visible():
            self.hide_settings()
            return
        self.show_settings()

    @Slot(object, str)
    def _on_save(self, config: AppConfig, api_key: str) -> None:
        self._config = config
        self._config_store.save(config)
        self._secret_store.save_api_key(api_key)
        self._sync_autostart()
        self.config_saved.emit(config, api_key)
        logger.info("Settings saved")

    @Slot()
    def _on_close(self) -> None:
        self.hide_settings()

    def _sync_autostart(self) -> None:
        provider = create_provider(self._launch_command)
        if self._config.autostart.enabled:
            provider.enable()
            return
        provider.disable()
