"""Album art normalization to a small JPEG."""

from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

COVER_SIZE = 200
COVER_JPEG_QUALITY = 80
BACKGROUND_MAX_EDGE = 1600
BACKGROUND_JPEG_QUALITY = 78
BACKGROUND_MAX_BYTES = 2_200_000


def to_cover_jpeg(raw: bytes | None) -> bytes | None:
    """Resize artwork to COVER_SIZE square JPEG, or None when unusable."""
    if not raw:
        return None
    try:
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
    except Exception:
        logger.warning("Cover decode failed")
        return None
    image = _fit_square(image, COVER_SIZE)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=COVER_JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


def to_background_jpeg(raw: bytes | None) -> bytes | None:
    """Downscale a site background image and encode it as JPEG under size cap."""
    if not raw:
        return None
    try:
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
    except Exception:
        logger.warning("Background decode failed")
        return None
    image = _fit_long_edge(image, BACKGROUND_MAX_EDGE)
    for quality in (BACKGROUND_JPEG_QUALITY, 70, 60, 50):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        data = buffer.getvalue()
        if len(data) <= BACKGROUND_MAX_BYTES:
            return data
    return buffer.getvalue()


def _fit_long_edge(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    edge = max(width, height)
    if edge <= max_edge:
        return image
    scale = max_edge / edge
    return image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)


def _fit_square(image: Image.Image, size: int) -> Image.Image:
    width, height = image.size
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    image = image.crop((left, top, left + edge, top + edge))
    return image.resize((size, size), Image.Resampling.LANCZOS)
