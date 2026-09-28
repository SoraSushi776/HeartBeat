"""截图采集参数"""

from __future__ import annotations

from dataclasses import dataclass

from heartbeat.protocol.models import (
    DEFAULT_SCREENSHOT_BLUR_RADIUS,
    DEFAULT_SCREENSHOT_METHOD,
    DEFAULT_SCREENSHOT_QUALITY,
    DEFAULT_SCREENSHOT_SCALE,
)


@dataclass(frozen=True)
class ScreenshotConfig:
    """截图降采样、模糊与编码参数"""

    blur_radius: float = DEFAULT_SCREENSHOT_BLUR_RADIUS
    scale: float = DEFAULT_SCREENSHOT_SCALE
    quality: int = DEFAULT_SCREENSHOT_QUALITY
    method: int = DEFAULT_SCREENSHOT_METHOD
