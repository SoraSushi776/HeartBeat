"""Guestbook message routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, func, select

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import get_session
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.models import Message
from heartbeat.server.schemas import MessageCreate, MessageList, MessageOut
from heartbeat.server.services.events import EventBus, StreamEvent
from heartbeat.server.services.ratelimit import RateLimiter
from heartbeat.server.services.status import StatusService
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/messages",
    tags=["messages"],
)

RATE_LIMIT_HITS = 5
RATE_LIMIT_WINDOW_S = 60.0


@router.get("")
def list_messages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return a paged guestbook list, newest first."""
    total = session.exec(select(func.count()).select_from(Message)).one()
    statement = select(Message).order_by(Message.created_ts.desc(), Message.id.desc())
    rows = session.exec(statement.offset(offset).limit(limit)).all()
    data = MessageList(
        items=[_to_out(row) for row in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )
    return ok(data.model_dump(mode="json"))


@router.post("")
def create_message(
    payload: MessageCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Store a guestbook message while the client is online."""
    _ensure_client_online(session)
    _ensure_within_rate_limit(request)
    row = Message(
        author=(payload.author or "").strip()[:50],
        content=payload.content,
        created_ts=current_ms(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Message created: id=%s author=%s", row.id, row.author or "anonymous")
    out = _to_out(row)
    EventBus.instance().publish(StreamEvent(event="message", data=out.model_dump(mode="json")))
    return ok(out.model_dump(mode="json"))


def _ensure_client_online(session: Session) -> None:
    """Reject writes when the tracked client has no fresh heartbeat."""
    service = StatusService.instance()
    client_id = service.resolve_client_id(session, None)
    status = service.build(session, client_id)
    if not status.online:
        raise ApiError(409, "Client offline")


def _ensure_within_rate_limit(request: Request) -> None:
    """Reject writes when the caller exceeds the sliding window cap."""
    host = request.client.host if request.client else "unknown"
    allowed = RateLimiter.instance().allow(host, RATE_LIMIT_HITS, RATE_LIMIT_WINDOW_S)
    if not allowed:
        raise ApiError(429, "Too many messages, slow down")


def _to_out(row: Message) -> MessageOut:
    """Convert a message row into the response model."""
    return MessageOut(
        id=int(row.id or 0),
        author=row.author,
        content=row.content,
        created_ts=row.created_ts,
    )
