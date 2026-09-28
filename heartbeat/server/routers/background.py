"""Site background upload and read routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.services import media_assets

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_PREFIX}/background", tags=["background"])

ALLOWED_TYPES = {
    "image/webp": "webp",
    "image/jpeg": "jpg",
    "image/png": "png",
}
MAX_BYTES = 2_500_000


@router.get("")
def get_background() -> dict[str, Any]:
    """Return the current site background URL when set."""
    url = media_assets.read_background_url()
    return ok({"url": url} if url else {})


@router.put("", dependencies=[Depends(require_api_key)])
async def upload_background(request: Request) -> dict[str, Any]:
    """Store a site background image uploaded from the client."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    suffix = ALLOWED_TYPES.get(content_type)
    if suffix is None:
        raise ApiError(400, "Unsupported image type")
    body = await request.body()
    if not body:
        raise ApiError(400, "Empty background body")
    if len(body) > MAX_BYTES:
        raise ApiError(413, "Background exceeds size limit")
    url = media_assets.save_background(body, suffix)
    logger.info("Background accepted: type=%s bytes=%d", content_type, len(body))
    return ok({"url": url})


@router.delete("", dependencies=[Depends(require_api_key)])
def clear_background() -> dict[str, Any]:
    """Remove the stored site background."""
    directory = media_assets.backgrounds_dir()
    if directory.is_dir():
        for path in directory.glob("site.*"):
            path.unlink(missing_ok=True)
    logger.info("Background cleared")
    return ok({"url": None})
