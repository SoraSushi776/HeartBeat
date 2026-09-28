"""macOS 依赖工具与系统权限检查"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

NOWPLAYING_URL = "https://github.com/kirtan-shah/nowplaying-cli"
BREW_INSTALL_CMD = "brew install nowplaying-cli"


class ToolStatus(str, Enum):
    MISSING = "missing"
    READY = "ready"
    UNKNOWN = "unknown"


class PermissionStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolCheck:
    name: str
    status: ToolStatus
    path: str | None
    hint: str


@dataclass(frozen=True)
class PermissionCheck:
    name: str
    status: PermissionStatus
    settings_path: str
    hint: str


def find_nowplaying_cli() -> str | None:
    candidates = (
        "nowplaying-cli",
        "/opt/homebrew/bin/nowplaying-cli",
        "/usr/local/bin/nowplaying-cli",
        os.path.expanduser("~/.local/bin/nowplaying-cli"),
    )
    for candidate in candidates:
        path = shutil.which(candidate) if "/" not in candidate else candidate
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def check_nowplaying_tool() -> ToolCheck:
    path = find_nowplaying_cli()
    if path:
        return ToolCheck("nowplaying-cli", ToolStatus.READY, path, "ok")
    return ToolCheck(
        "nowplaying-cli",
        ToolStatus.MISSING,
        None,
        f"install via Homebrew: {BREW_INSTALL_CMD}  ({NOWPLAYING_URL})",
    )


def check_homebrew() -> ToolCheck:
    path = shutil.which("brew")
    if path:
        return ToolCheck("homebrew", ToolStatus.READY, path, "ok")
    return ToolCheck("homebrew", ToolStatus.MISSING, None, "install from https://brew.sh")


def run_tool_install() -> tuple[bool, str]:
    brew = shutil.which("brew")
    if not brew:
        return False, "Homebrew not found"
    try:
        result = subprocess.run(
            [brew, "install", "nowplaying-cli"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.exception("brew install failed")
        return False, str(exc)
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, result.stdout.strip()


def open_screen_recording_settings() -> None:
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ],
        check=False,
    )


def open_automation_settings() -> None:
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation",
        ],
        check=False,
    )


def probe_screenshot_permission() -> PermissionCheck:
    try:
        from mss import MSS

        with MSS() as sct:
            sct.grab(sct.monitors[0])
        return PermissionCheck(
            "screen_recording",
            PermissionStatus.GRANTED,
            "Privacy_ScreenCapture",
            "ok",
        )
    except Exception:
        logger.exception("screenshot probe failed")
        return PermissionCheck(
            "screen_recording",
            PermissionStatus.DENIED,
            "Privacy_ScreenCapture",
            "grant Screen Recording to this app in System Settings",
        )


def probe_automation_permission() -> PermissionCheck:
    script = 'tell application "System Events" to return name of first process'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return PermissionCheck(
            "automation",
            PermissionStatus.UNKNOWN,
            "Privacy_Automation",
            "unable to probe Automation permission",
        )
    if result.returncode == 0:
        return PermissionCheck("automation", PermissionStatus.GRANTED, "Privacy_Automation", "ok")
    denied = "-1743" in (result.stderr or "") or "not allowed" in (result.stderr or "").lower()
    status = PermissionStatus.DENIED if denied else PermissionStatus.UNKNOWN
    return PermissionCheck(
        "automation",
        status,
        "Privacy_Automation",
        "grant Automation permission for Music/Spotify/System Events",
    )


def collect_setup_report() -> dict[str, object]:
    tools = [check_nowplaying_tool(), check_homebrew()]
    permissions = [probe_screenshot_permission(), probe_automation_permission()]
    return {
        "tools": [
            {"name": t.name, "status": t.status.value, "path": t.path, "hint": t.hint}
            for t in tools
        ],
        "permissions": [
            {
                "name": p.name,
                "status": p.status.value,
                "settings_path": p.settings_path,
                "hint": p.hint,
            }
            for p in permissions
        ],
    }
