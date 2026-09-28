from __future__ import annotations

import logging
import os
from pathlib import Path

from heartbeat.client.autostart.base import APP_LABEL, DESKTOP_FILE_NAME

logger = logging.getLogger(__name__)


class LinuxAutostartProvider:
    """Register autostart via an XDG desktop entry."""

    def __init__(self, command: str) -> None:
        self._command = command
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        self._entry_path = base / "autostart" / DESKTOP_FILE_NAME

    def enable(self) -> None:
        """Write the autostart desktop entry."""
        self._entry_path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_LABEL}\n"
            f"Exec={self._command}\n"
            "Hidden=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        self._entry_path.write_text(content, encoding="utf-8")
        logger.info("Linux autostart enabled: %s", self._entry_path)

    def disable(self) -> None:
        """Mark the desktop entry hidden or remove it."""
        if not self._entry_path.exists():
            logger.info("Linux autostart entry already absent")
            return
        content = self._entry_path.read_text(encoding="utf-8")
        self._entry_path.write_text(
            content.replace("Hidden=false", "Hidden=true"), encoding="utf-8"
        )
        logger.info("Linux autostart disabled")

    def is_enabled(self) -> bool:
        """Return whether the desktop entry exists and is not hidden."""
        if not self._entry_path.exists():
            return False
        content = self._entry_path.read_text(encoding="utf-8")
        return "Hidden=true" not in content


def create_provider(command: str | list[str], working_directory: str | None = None) -> LinuxAutostartProvider:
    """Create the Linux autostart provider."""
    if isinstance(command, str):
        return LinuxAutostartProvider(command)
    parts = [f"'{item}'" if " " in item else item for item in command]
    return LinuxAutostartProvider(" ".join(parts))
