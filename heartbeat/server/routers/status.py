"""Realtime status and SSE stream routes."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterable
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlmodel import Session

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.db import create_session
from heartbeat.server.dependencies import get_session
from heartbeat.server.envelope import ok
from heartbeat.server.services.events import EventBus
from heartbeat.server.services.status import StatusService

logger = logging.getLogger(__name__)

router = APIRouter(prefix=API_PREFIX, tags=["status"])

STATUS_PATH = "/status"
STREAM_PATH = "/stream"
STREAM_POLL_S = 15.0


@router.get(STATUS_PATH)
def get_status(
    client_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return the assembled realtime status for a client."""
    service = StatusService.instance()
    resolved = service.resolve_client_id(session, client_id)
    status = service.build(session, resolved)
    return ok(status.model_dump(mode="json"))


@router.get(STREAM_PATH, response_class=EventSourceResponse)
async def stream_status(client_id: str | None = None) -> AsyncIterable[ServerSentEvent]:
    """Push status, heartbeat and snapshot events over SSE."""
    initial = _initial_status(client_id)
    bus = EventBus.instance()
    queue = bus.subscribe()
    try:
        yield ServerSentEvent(event="status", data=initial)
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=STREAM_POLL_S)
                yield ServerSentEvent(event=item.event, data=item.data)
            except asyncio.TimeoutError:
                yield ServerSentEvent(comment="keepalive")
    finally:
        bus.unsubscribe(queue)


def _initial_status(client_id: str | None) -> dict[str, Any]:
    """Build the first status payload for the SSE stream."""
    service = StatusService.instance()
    session = create_session()
    try:
        resolved = service.resolve_client_id(session, client_id)
        return service.build(session, resolved).model_dump(mode="json")
    finally:
        session.close()
