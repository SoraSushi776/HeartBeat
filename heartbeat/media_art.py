"""Album art normalization to a small JPEG."""

from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

COVER_SIZE = 200
COVER_JPEG_QUALITY = 80


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


def _fit_square(image: Image.Image, size: int) -> Image.Image:
    width, height = image.size
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    image = image.crop((left, top, left + edge, top + edge))
    return image.resize((size, size), Image.Resampling.LANCZOS)
