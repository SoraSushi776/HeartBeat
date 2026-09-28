from __future__ import annotations

import logging
import winreg

from heartbeat.client.autostart.base import APP_LABEL

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class WindowsAutostartProvider:
    """Register autostart via the HKCU Run key."""

    def __init__(self, command: str) -> None:
        self._command = command

    def enable(self) -> None:
        """Write the Run key entry."""
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.SetValueEx(key, APP_LABEL, 0, winreg.REG_SZ, self._command)
        logger.info("Windows autostart enabled")

    def disable(self) -> None:
        """Remove the Run key entry."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_LABEL)
        except FileNotFoundError:
            logger.info("Windows autostart entry already absent")
            return
        logger.info("Windows autostart disabled")

    def is_enabled(self) -> bool:
        """Return whether the Run key entry exists."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_LABEL)
            return True
        except OSError:
            return False


def create_provider(command: str | list[str], working_directory: str | None = None) -> WindowsAutostartProvider:
    """Create the Windows autostart provider."""
    if isinstance(command, str):
        return WindowsAutostartProvider(command)
    parts = [f'"{item}"' if " " in item else item for item in command]
    return WindowsAutostartProvider(" ".join(parts))
