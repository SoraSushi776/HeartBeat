from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

APP_DIR_NAME = "HeartBeat"
CONFIG_FILE_NAME = "client.json"
SECRETS_FILE_NAME = "client.secrets.json"

_PLATFORM_DIRS: dict[str, str] = {
    "win32": "windows",
    "darwin": "macos",
    "linux": "linux",
}


def platform_key() -> str:
    """Return windows, macos, or linux for the running system."""
    return _PLATFORM_DIRS.get(sys.platform, "linux")


def _windows_config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / APP_DIR_NAME


def _macos_config_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / APP_DIR_NAME


def _linux_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "heartbeat"


_DIR_BUILDERS: dict[str, Callable[[], Path]] = {
    "windows": _windows_config_dir,
    "macos": _macos_config_dir,
    "linux": _linux_config_dir,
}


def config_dir() -> Path:
    """Return the platform config directory for HeartBeat client files."""
    return _DIR_BUILDERS[platform_key()]()


def config_path() -> Path:
    """Return the main client.json path."""
    return config_dir() / CONFIG_FILE_NAME


def secrets_path() -> Path:
    """Return the client.secrets.json path."""
    return config_dir() / SECRETS_FILE_NAME


def ensure_config_dir() -> Path:
    """Create the config directory when missing and return it."""
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory
