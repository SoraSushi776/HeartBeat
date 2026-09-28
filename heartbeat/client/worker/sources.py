from __future__ import annotations

import logging
from dataclasses import dataclass

from heartbeat.adapters.base import MediaAdapter, ProcessAdapter, ScreenshotAdapter, SystemAdapter
from heartbeat.adapters.media import get_media_adapter
from heartbeat.adapters.processes import get_process_adapter
from heartbeat.adapters.screenshot import ScreenshotConfig as AdapterScreenshotConfig
from heartbeat.adapters.screenshot import get_screenshot_adapter
from heartbeat.adapters.system import get_system_adapter
from heartbeat.client.config.models import ScreenshotConfig

logger = logging.getLogger(__name__)


@dataclass
class CollectorBundle:
    screenshot: ScreenshotAdapter
    media: MediaAdapter
    processes: ProcessAdapter
    system: SystemAdapter


def to_adapter_screenshot(config: ScreenshotConfig) -> AdapterScreenshotConfig:
    """Map client screenshot settings onto adapter capture parameters."""
    return AdapterScreenshotConfig(
        blur_radius=config.blur_radius,
        scale=config.scale,
        quality=config.quality,
    )


def create_collectors(
    process_whitelist: list[str],
    screenshot: ScreenshotConfig,
) -> CollectorBundle:
    """Create platform collectors from heartbeat.adapters factories."""
    logger.info("Creating collectors via heartbeat.adapters")
    return CollectorBundle(
        screenshot=get_screenshot_adapter(to_adapter_screenshot(screenshot)),
        media=get_media_adapter(),
        processes=get_process_adapter(process_whitelist),
        system=get_system_adapter(),
    )
