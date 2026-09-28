"""媒体采集适配器工厂"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from heartbeat.adapters.base import MediaAdapter
from heartbeat.adapters.media.linux import LinuxMediaAdapter
from heartbeat.adapters.media.macos import MacosMediaAdapter
from heartbeat.adapters.media.windows import WindowsMediaAdapter
from heartbeat.adapters.platform import current_platform
from heartbeat.protocol.models import Platform

_BUILDERS: dict[Platform, Callable[[], MediaAdapter]] = {
    Platform.WINDOWS: WindowsMediaAdapter,
    Platform.MACOS: MacosMediaAdapter,
    Platform.LINUX: LinuxMediaAdapter,
}


@lru_cache(maxsize=1)
def get_media_adapter() -> MediaAdapter:
    """返回当前平台媒体采集适配器"""
    return _BUILDERS[current_platform()]()
