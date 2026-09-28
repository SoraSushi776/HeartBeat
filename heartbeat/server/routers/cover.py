"""Album art upload routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.services import media_assets

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/cover",
    tags=["cover"],
    dependencies=[Depends(require_api_key)],
)

JPEG_CONTENT_TYPE = "image/jpeg"
MAX_BYTES = 256_000


@router.put("/{client_id}")
async def upload_cover(client_id: str, request: Request) -> dict[str, Any]:
    """Store the client's 200x200 JPEG album art."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type != JPEG_CONTENT_TYPE:
        raise ApiError(400, "Content-Type must be image/jpeg")
    body = await request.body()
    if not body:
        raise ApiError(400, "Empty cover body")
    if len(body) > MAX_BYTES:
        raise ApiError(413, "Cover exceeds size limit")
    url = media_assets.save_cover(client_id, body)
    logger.info("Cover accepted: client=%s", client_id)
    return ok({"url": url})
