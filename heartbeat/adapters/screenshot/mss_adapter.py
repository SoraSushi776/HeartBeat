"""mss 截图采集与本地模糊编码"""

from __future__ import annotations

import io
import logging

from mss import MSS
from PIL import Image, ImageFilter

from heartbeat.adapters.privacy import PrivacyGate
from heartbeat.adapters.screenshot.config import ScreenshotConfig
from heartbeat.protocol.models import Capability, ScreenshotResult

logger = logging.getLogger(__name__)


class MssScreenshotAdapter:
    """mss 抓帧，PIL 降采样高斯模糊后编码 WebP"""

    def __init__(self, config: ScreenshotConfig | None = None) -> None:
        self._config = config or ScreenshotConfig()

    def collect(self, gate: PrivacyGate) -> ScreenshotResult | None:
        """采集截图，隐私关闭时返回 None"""
        if not gate.allow(Capability.SCREENSHOT):
            return None
        return self._capture()

    def _capture(self) -> ScreenshotResult:
        raw = self._grab()
        img = self._downsample(raw)
        img = img.filter(ImageFilter.GaussianBlur(radius=self._config.blur_radius))
        return self._encode(img)

    def _grab(self) -> Image.Image:
        with MSS() as sct:
            shot = sct.grab(sct.monitors[1])
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    def _downsample(self, img: Image.Image) -> Image.Image:
        width = max(1, int(img.width * self._config.scale))
        height = max(1, int(img.height * self._config.scale))
        return img.resize((width, height), Image.Resampling.LANCZOS)

    def _encode(self, img: Image.Image) -> ScreenshotResult:
        buf = io.BytesIO()
        img.save(
            buf,
            format="WEBP",
            quality=self._config.quality,
            method=self._config.method,
        )
        logger.debug("Screenshot encoded: %dx%d", img.width, img.height)
        return ScreenshotResult(webp=buf.getvalue(), width=img.width, height=img.height)
