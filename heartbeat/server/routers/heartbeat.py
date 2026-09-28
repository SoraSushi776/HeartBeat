"""Heartbeat ingestion routes."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from heartbeat.protocol.models import API_PREFIX, Capability, PrivacyFlags
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ok
from heartbeat.server.models import Heartbeat
from heartbeat.server.schemas import HeartbeatAccepted, HeartbeatIn
from heartbeat.server.services.events import EventBus, StreamEvent
from heartbeat.server.services.status import StatusService
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/heartbeat",
    tags=["heartbeat"],
    dependencies=[Depends(require_api_key)],
)


@router.post("")
def create_heartbeat(
    payload: HeartbeatIn,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Store a client heartbeat snapshot and return the screenshot upload hint."""
    received_ts = current_ms()
    stored = to_stored_payload(payload)
    row = Heartbeat(
        ts=payload.ts,
        client_id=payload.client.id,
        payload_json=json.dumps(stored),
        screenshot_path=None,
    )
    session.add(row)
    session.commit()
    logger.info("Heartbeat stored: client=%s ts=%d", payload.client.id, payload.ts)
    _publish_events(session, payload, stored)
    data = HeartbeatAccepted(received_ts=received_ts)
    if payload.privacy.screenshot:
        data.screenshot_upload_url = f"{API_PREFIX}/screenshot/{payload.client.id}"
        data.screenshot_expires_in = 60
    return ok(data.model_dump(mode="json"))


def to_stored_payload(payload: HeartbeatIn) -> dict[str, Any]:
    """Return the privacy-filtered payload that should be persisted."""
    flags = PrivacyFlags(
        screenshot=payload.privacy.screenshot,
        media=payload.privacy.media,
        processes=payload.privacy.processes,
        system=payload.privacy.system,
    )
    data: dict[str, Any] = {
        "ts": payload.ts,
        "client": payload.client.model_dump(mode="json"),
        "privacy": flags.to_dict(),
    }
    data["system"] = (
        payload.system.model_dump(mode="json")
        if flags.allows(Capability.SYSTEM) and payload.system is not None
        else None
    )
    data["media"] = (
        payload.media.model_dump(mode="json")
        if flags.allows(Capability.MEDIA) and payload.media is not None
        else None
    )
    data["processes"] = (
        [item.model_dump(mode="json") for item in payload.processes]
        if flags.allows(Capability.PROCESSES)
        else []
    )
    return data


def _publish_events(session: Session, payload: HeartbeatIn, stored: dict[str, Any]) -> None:
    """Broadcast heartbeat and status events to SSE subscribers."""
    bus = EventBus.instance()
    bus.publish(StreamEvent(event="heartbeat", data=stored))
    status = StatusService.instance().build(session, payload.client.id)
    bus.publish(StreamEvent(event="status", data=status.model_dump(mode="json")))
