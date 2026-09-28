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

    def __init__(self, program_arguments: list[str], working_directory: str | None = None) -> None:
        self._program_arguments = list(program_arguments)
        self._working_directory = working_directory
        self._plist_path = Path.home() / "Library" / "LaunchAgents" / PLIST_NAME

    def enable(self) -> None:
        """Write the LaunchAgent plist and bootstrap it."""
        self._plist_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {
            "Label": APP_LABEL,
            "ProgramArguments": self._program_arguments,
            "RunAtLoad": True,
        }
        if self._working_directory:
            payload["WorkingDirectory"] = self._working_directory
        with self._plist_path.open("wb") as handle:
            plistlib.dump(payload, handle)
        self._launchctl(["bootout", self._gui_domain(), str(self._plist_path)])
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
            result = subprocess.run(["launchctl", *args], check=False, capture_output=True, text=True)
        except OSError:
            logger.exception("launchctl failed: %s", args)
            return
        if result.returncode != 0:
            logger.warning("launchctl %s failed: %s", args, (result.stderr or result.stdout).strip())


def create_provider(command: str | list[str], working_directory: str | None = None) -> MacosAutostartProvider:
    """Create the macOS autostart provider."""
    if isinstance(command, str):
        arguments = command.split()
    else:
        arguments = list(command)
    return MacosAutostartProvider(arguments, working_directory)
