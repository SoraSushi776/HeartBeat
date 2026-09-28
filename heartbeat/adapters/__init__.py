"""跨平台采集适配层"""

from heartbeat.adapters.base import (
    MediaAdapter,
    ProcessAdapter,
    ScreenshotAdapter,
    SystemAdapter,
)
from heartbeat.adapters.media import get_media_adapter
from heartbeat.adapters.platform import current_platform
from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.adapters.processes import ProcessFilter, get_process_adapter
from heartbeat.adapters.screenshot import ScreenshotConfig, get_screenshot_adapter
from heartbeat.adapters.system import get_system_adapter

__all__ = [
    "MediaAdapter",
    "PrivacyGate",
    "ProcessAdapter",
    "ProcessFilter",
    "ScreenshotAdapter",
    "ScreenshotConfig",
    "SystemAdapter",
    "current_platform",
    "get_media_adapter",
    "get_process_adapter",
    "get_screenshot_adapter",
    "get_system_adapter",
]
