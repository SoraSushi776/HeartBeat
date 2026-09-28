from __future__ import annotations

import logging
import os
import plistlib
import subprocess
from pathlib import Path

from heartbeat.client.autostart.base import APP_LABEL

logger = logging.getLogger(__name__)

PLIST_NAME = f"{APP_LABEL}.plist"


class MacosAutostartProvider:
    """Register autostart via a LaunchAgent plist."""

    def __init__(self, command: str) -> None:
        self._command = command
        self._plist_path = Path.home() / "Library" / "LaunchAgents" / PLIST_NAME

    def enable(self) -> None:
        """Write the LaunchAgent plist and bootstrap it."""
        self._plist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "Label": APP_LABEL,
            "ProgramArguments": [self._command],
            "RunAtLoad": True,
        }
        with self._plist_path.open("wb") as handle:
            plistlib.dump(payload, handle)
        self._launchctl(["bootstrap", self._gui_domain(), str(self._plist_path)])
        logger.info("macOS autostart enabled: %s", self._plist_path)

    def disable(self) -> None:
        """Bootout the LaunchAgent and remove the plist."""
        self._launchctl(["bootout", self._gui_domain(), str(self._plist_path)])
        if self._plist_path.exists():
            self._plist_path.unlink()
        logger.info("macOS autostart disabled")

    def is_enabled(self) -> bool:
        """Return whether the LaunchAgent plist exists."""
        return self._plist_path.exists()

    def _gui_domain(self) -> str:
        return f"gui/{os.getuid()}"

    def _launchctl(self, args: list[str]) -> None:
        try:
            subprocess.run(["launchctl", *args], check=False, capture_output=True)
        except OSError:
            logger.exception("launchctl failed: %s", args)


def create_provider(command: str) -> MacosAutostartProvider:
    """Create the macOS autostart provider."""
    return MacosAutostartProvider(command)
