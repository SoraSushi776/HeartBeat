"""截图采集"""

from heartbeat.adapters.screenshot.config import ScreenshotConfig
from heartbeat.adapters.screenshot.factory import get_screenshot_adapter

__all__ = ["ScreenshotConfig", "get_screenshot_adapter"]
