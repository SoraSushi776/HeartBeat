from __future__ import annotations

import importlib
import logging
from typing import Protocol

from heartbeat.client.config.paths import platform_key

logger = logging.getLogger(__name__)

APP_LABEL = "com.heartbeat.client"
DESKTOP_FILE_NAME = "heartbeat-client.desktop"


class AutostartProvider(Protocol):
    """Platform autostart registration backend."""

    def enable(self) -> None:
        """Register the application for launch at login."""

    def disable(self) -> None:
        """Remove the launch at login registration."""

    def is_enabled(self) -> bool:
        """Return whether launch at login is currently registered."""


_PLATFORM_MODULES: dict[str, str] = {
    "windows": "heartbeat.client.autostart.windows",
    "macos": "heartbeat.client.autostart.macos",
    "linux": "heartbeat.client.autostart.linux",
}


def create_provider(command: str) -> AutostartProvider:
    """Create the platform autostart provider for the given launch command."""
    module_name = _PLATFORM_MODULES[platform_key()]
    module = importlib.import_module(module_name)
    factory = module.create_provider
    return factory(command)
