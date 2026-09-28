"""Album art and site background file storage."""

from __future__ import annotations

import logging
from pathlib import Path

from heartbeat.server.config import get_settings

logger = logging.getLogger(__name__)

COVER_SUFFIX = "jpg"
BACKGROUND_SUFFIX = "webp"


def covers_dir() -> Path:
    return get_settings().data_dir / "covers"


def backgrounds_dir() -> Path:
    return get_settings().data_dir / "backgrounds"


def save_cover(client_id: str, jpeg: bytes) -> str:
    """Write the latest cover JPEG and return its public URL."""
    directory = covers_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{client_id}.{COVER_SUFFIX}"
    path.write_bytes(jpeg)
    logger.info("Cover stored: client=%s bytes=%d", client_id, len(jpeg))
    return cover_url(client_id)


def cover_url(client_id: str) -> str:
    return f"/static/covers/{client_id}.{COVER_SUFFIX}"


def save_background(image: bytes, suffix: str = BACKGROUND_SUFFIX) -> str:
    """Write the site background image and return its public URL."""
    directory = backgrounds_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"site.{suffix}"
    path.write_bytes(image)
    logger.info("Background stored: bytes=%d", len(image))
    return background_url(suffix)


def background_url(suffix: str = BACKGROUND_SUFFIX) -> str:
    return f"/static/backgrounds/site.{suffix}"


def read_background_url() -> str | None:
    directory = backgrounds_dir()
    for suffix in ("webp", "jpg", "jpeg", "png"):
        if (directory / f"site.{suffix}").is_file():
            return background_url(suffix)
    return None
