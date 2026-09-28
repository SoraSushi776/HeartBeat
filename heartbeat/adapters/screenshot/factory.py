"""截图采集适配器工厂"""

from __future__ import annotations

from heartbeat.adapters.base import ScreenshotAdapter
from heartbeat.adapters.platform import current_platform
from heartbeat.adapters.screenshot.config import ScreenshotConfig
from heartbeat.adapters.screenshot.mss_adapter import MssScreenshotAdapter
from heartbeat.protocol.models import Platform

_BUILDERS: dict[Platform, type[MssScreenshotAdapter]] = {
    Platform.WINDOWS: MssScreenshotAdapter,
    Platform.MACOS: MssScreenshotAdapter,
    Platform.LINUX: MssScreenshotAdapter,
}


def get_screenshot_adapter(config: ScreenshotConfig | None = None) -> ScreenshotAdapter:
    """返回当前平台截图采集适配器，config 为可选采集参数"""
    return _BUILDERS[current_platform()](config)
