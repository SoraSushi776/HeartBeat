"""Guestbook message routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, delete, func, select

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.models import Message, MessageBan
from heartbeat.server.schemas import (
    BanCreate,
    BanList,
    BanOut,
    MessageAdminList,
    MessageAdminOut,
    MessageCreate,
    MessageList,
    MessageOut,
)
from heartbeat.server.services.events import EventBus, StreamEvent
from heartbeat.server.services.ip_location import IpLocationService, client_ip_from_headers
from heartbeat.server.services.ratelimit import RateLimiter
from heartbeat.server.services.status import StatusService
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/messages",
    tags=["messages"],
)

write_deps = [Depends(require_api_key)]

RATE_LIMIT_HITS = 5
RATE_LIMIT_WINDOW_S = 60.0


@router.get("")
def list_messages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return a paged guestbook list, newest first, without raw IPs."""
    total = session.exec(select(func.count()).select_from(Message)).one()
    statement = select(Message).order_by(Message.created_ts.desc(), Message.id.desc())
    rows = session.exec(statement.offset(offset).limit(limit)).all()
    data = MessageList(
        items=[_to_public_out(row) for row in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )
    return ok(data.model_dump(mode="json"))


@router.get("/admin", dependencies=write_deps)
def list_messages_admin(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return a paged guestbook list with IP and location for the admin client."""
    total = session.exec(select(func.count()).select_from(Message)).one()
    statement = select(Message).order_by(Message.created_ts.desc(), Message.id.desc())
    rows = session.exec(statement.offset(offset).limit(limit)).all()
    data = MessageAdminList(
        items=[_to_admin_out(row) for row in rows],
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
    ip = _client_ip(request)
    _ensure_not_banned(session, ip)
    _ensure_client_online(session)
    _ensure_within_rate_limit(ip)
    location = IpLocationService.instance().resolve(ip)
    row = Message(
        author=(payload.author or "").strip()[:50],
        content=payload.content,
        created_ts=current_ms(),
        ip=ip,
        location=location,
        expose_ip=payload.expose_ip,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Message created: id=%s author=%s", row.id, row.author or "anonymous")
    out = _to_public_out(row)
    EventBus.instance().publish(StreamEvent(event="message", data=out.model_dump(mode="json")))
    return ok(out.model_dump(mode="json"))


@router.get("/bans", dependencies=write_deps)
def list_bans(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return every banned guestbook IP."""
    rows = session.exec(select(MessageBan).order_by(MessageBan.created_ts.desc())).all()
    data = BanList(items=[_to_ban_out(row) for row in rows])
    return ok(data.model_dump(mode="json"))


@router.post("/bans", dependencies=write_deps)
def create_ban(payload: BanCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Ban a guestbook IP so it can no longer post."""
    ip = payload.ip.strip()
    existing = session.exec(select(MessageBan).where(MessageBan.ip == ip)).first()
    if existing is not None:
        return ok(_to_ban_out(existing).model_dump(mode="json"))
    row = MessageBan(ip=ip, created_ts=current_ms())
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Guestbook IP banned: id=%s ip=%s", row.id, row.ip)
    return ok(_to_ban_out(row).model_dump(mode="json"))


@router.delete("/bans/{ban_id}", dependencies=write_deps)
def delete_ban(ban_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Remove one guestbook IP ban."""
    row = session.get(MessageBan, ban_id)
    if row is None:
        raise ApiError(404, "Ban not found")
    session.exec(delete(MessageBan).where(MessageBan.id == ban_id))
    session.commit()
    logger.info("Guestbook IP unbanned: id=%s ip=%s", ban_id, row.ip)
    return ok({"id": ban_id})


@router.delete("/{message_id}", dependencies=write_deps)
def delete_message(message_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Delete one guestbook message."""
    row = session.get(Message, message_id)
    if row is None:
        raise ApiError(404, "Message not found")
    session.exec(delete(Message).where(Message.id == message_id))
    session.commit()
    logger.info("Message deleted: id=%s", message_id)
    return ok({"id": message_id})


def _client_ip(request: Request) -> str:
    """Return the caller IP, honouring X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    direct = request.client.host if request.client else None
    return client_ip_from_headers(forwarded, direct)


def _ensure_not_banned(session: Session, ip: str) -> None:
    """Reject writes from an IP present in the ban table."""
    row = session.exec(select(MessageBan).where(MessageBan.ip == ip)).first()
    if row is not None:
        raise ApiError(403, "IP banned")


def _ensure_client_online(session: Session) -> None:
    """Reject writes when the tracked client has no fresh heartbeat."""
    service = StatusService.instance()
    client_id = service.resolve_client_id(session, None)
    status = service.build(session, client_id)
    if not status.online:
        raise ApiError(409, "Client offline")


def _ensure_within_rate_limit(ip: str) -> None:
    """Reject writes when the caller exceeds the sliding window cap."""
    allowed = RateLimiter.instance().allow(ip or "unknown", RATE_LIMIT_HITS, RATE_LIMIT_WINDOW_S)
    if not allowed:
        raise ApiError(429, "Too many messages, slow down")


def _to_public_out(row: Message) -> MessageOut:
    """Convert a message row into the public response model."""
    return MessageOut(
        id=int(row.id or 0),
        author=row.author,
        content=row.content,
        created_ts=row.created_ts,
        expose_ip=row.expose_ip,
        location=row.location if row.expose_ip else None,
    )


def _to_admin_out(row: Message) -> MessageAdminOut:
    """Convert a message row into the admin response model."""
    return MessageAdminOut(
        id=int(row.id or 0),
        author=row.author,
        content=row.content,
        created_ts=row.created_ts,
        ip=row.ip,
        location=row.location,
        expose_ip=row.expose_ip,
    )


def _to_ban_out(row: MessageBan) -> BanOut:
    """Convert a ban row into the response model."""
    return BanOut(
        id=int(row.id or 0),
        ip=row.ip,
        created_ts=row.created_ts,
    )
