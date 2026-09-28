"""采集适配器协议"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.protocol.models import MediaInfo, ProcessInfo, ScreenshotResult, SystemInfo


@runtime_checkable
class ScreenshotAdapter(Protocol):
    """截图采集适配器"""

    def collect(self, gate: PrivacyGate) -> ScreenshotResult | None:
        """采集截图，隐私关闭时返回 None"""
        ...


@runtime_checkable
class MediaAdapter(Protocol):
    """媒体播放采集适配器"""

    def collect(self, gate: PrivacyGate) -> MediaInfo | None:
        """采集正在播放，隐私关闭时返回 None"""
        ...


@runtime_checkable
class ProcessAdapter(Protocol):
    """进程列表采集适配器"""

    def collect(self, gate: PrivacyGate) -> list[ProcessInfo] | None:
        """采集白名单进程，隐私关闭时返回 None"""
        ...


@runtime_checkable
class SystemAdapter(Protocol):
    """系统负载采集适配器"""

    def collect(self, gate: PrivacyGate) -> SystemInfo | None:
        """采集系统负载，隐私关闭时返回 None"""
        ...
