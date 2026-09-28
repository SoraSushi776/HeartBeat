"""Platform system notification dispatch."""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable

from heartbeat.adapters.platform import current_platform
from heartbeat.protocol.models import Platform

logger = logging.getLogger(__name__)

CommandBuilder = Callable[[str, str], list[str]]


def _apple_string(text: str) -> str:
    """Quote text as an AppleScript string literal."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _ps_single_quote(text: str) -> str:
    """Quote text as a PowerShell single-quoted string literal."""
    return f"'{text.replace(chr(39), chr(39) * 2)}'"


def _xml_escape(text: str) -> str:
    """Escape text for embedding inside an XML toast template."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def macos_command(title: str, message: str) -> list[str]:
    """Build the osascript notification command for title and message."""
    script = f"display notification {_apple_string(message)} with title {_apple_string(title)}"
    return ["osascript", "-e", script]


def windows_command(title: str, message: str) -> list[str]:
    """Build the PowerShell toast command for title and message."""
    toast_xml = (
        "<toast><visual><binding template=\"ToastText02\">"
        f"<text id=\"1\">{_xml_escape(title)}</text>"
        f"<text id=\"2\">{_xml_escape(message)}</text>"
        "</binding></visual></toast>"
    )
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
        " ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument,"
        " ContentType = WindowsRuntime] | Out-Null; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        f"$xml.LoadXml({_ps_single_quote(toast_xml)}); "
        "$toast = New-Object Windows.UI.Notifications.ToastNotification($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier"
        f"({_ps_single_quote('HeartBeat')}).Show($toast)"
    )
    return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]


def linux_command(title: str, message: str) -> list[str]:
    """Build the notify-send command for title and message."""
    return ["notify-send", "--app-name=HeartBeat", title, message]


_COMMANDS: dict[Platform, CommandBuilder] = {
    Platform.MACOS: macos_command,
    Platform.WINDOWS: windows_command,
    Platform.LINUX: linux_command,
}


def notification_command(title: str, message: str) -> list[str]:
    """Build the notification argv for the current platform."""
    return _COMMANDS[current_platform()](title, message)


def show_notification(title: str, message: str) -> None:
    """Show a system notification for title and message without blocking the caller."""
    command = notification_command(title, message)
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        logger.warning("Notification command failed: %s", command[0])
        return
    logger.debug("Notification shown: %s", title)
