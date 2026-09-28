"""Screenshot upload routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlmodel import Session, select

from heartbeat.protocol.models import API_PREFIX, HEADER_HEARTBEAT_TS
from heartbeat.server.config import get_settings
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.models import Heartbeat
from heartbeat.server.schemas import ScreenshotStored
from heartbeat.server.services.events import EventBus, StreamEvent
from heartbeat.server.services.snapshots import SnapshotStore
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/screenshot",
    tags=["screenshot"],
    dependencies=[Depends(require_api_key)],
)

WEBP_CONTENT_TYPE = "image/webp"


@router.put("/{client_id}")
async def upload_screenshot(
    client_id: str,
    request: Request,
    session: Session = Depends(get_session),
    heartbeat_ts: str | None = Header(default=None, alias=HEADER_HEARTBEAT_TS),
) -> dict[str, Any]:
    """Store a blurred WebP snapshot for the given client."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type != WEBP_CONTENT_TYPE:
        raise ApiError(400, "Content-Type must be image/webp")
    body = await request.body()
    settings = get_settings()
    if len(body) > settings.screenshot_max_bytes:
        raise ApiError(413, "Screenshot exceeds size limit")
    if not body:
        raise ApiError(400, "Empty screenshot body")
    ts = _resolve_ts(heartbeat_ts)
    info = SnapshotStore.instance().save_latest(client_id, body, ts)
    _link_heartbeat(session, client_id, ts, info.path.name)
    logger.info("Screenshot accepted: client=%s bytes=%d", client_id, len(body))
    data = ScreenshotStored(url=info.url, ts=info.ts)
    EventBus.instance().publish(
        StreamEvent(
            event="snapshot",
            data={"client_id": client_id, "ts": info.ts, "url": info.url},
        )
    )
    return ok(data.model_dump(mode="json"))


def _resolve_ts(header_value: str | None) -> int:
    """Return the heartbeat ts from the header or the current clock."""
    if header_value is None:
        return current_ms()
    try:
        parsed = int(header_value)
    except ValueError:
        raise ApiError(400, "X-Heartbeat-Ts must be an integer") from None
    if parsed < 0:
        raise ApiError(400, "X-Heartbeat-Ts must be non-negative")
    return parsed


def _link_heartbeat(session: Session, client_id: str, ts: int, filename: str) -> None:
    """Attach the screenshot path to the matching heartbeat row when present."""
    statement = (
        select(Heartbeat)
        .where(Heartbeat.client_id == client_id, Heartbeat.ts == ts)
        .order_by(Heartbeat.id.desc())
    )
    row = session.exec(statement).first()
    if row is None:
        return
    row.screenshot_path = f"snapshots/{filename}"
    session.add(row)
    session.commit()
