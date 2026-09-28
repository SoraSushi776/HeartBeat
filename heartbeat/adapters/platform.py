"""当前平台标识解析"""

from __future__ import annotations

import sys

from heartbeat.protocol.models import Platform

_PLATFORM_MAP: dict[str, Platform] = {
    "win32": Platform.WINDOWS,
    "darwin": Platform.MACOS,
    "linux": Platform.LINUX,
}


def current_platform() -> Platform:
    """解析 sys.platform 得到当前平台枚举，未知平台报错"""
    try:
        return _PLATFORM_MAP[sys.platform]
    except KeyError:
        raise ValueError(f"unsupported platform: {sys.platform}") from None
