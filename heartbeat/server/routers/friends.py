"""Friend link CRUD routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.models import Friend
from heartbeat.server.schemas import FriendCreate, FriendOut, FriendUpdate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/friends",
    tags=["friends"],
)

write_deps = [Depends(require_api_key)]


@router.get("")
def list_friends(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return friend links ordered by sort weight."""
    rows = session.exec(select(Friend).order_by(Friend.sort.asc(), Friend.id.asc())).all()
    return ok([_to_out(row).model_dump(mode="json") for row in rows])


@router.post("", dependencies=write_deps)
def create_friend(
    payload: FriendCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Create a friend link."""
    row = Friend(
        name=payload.name,
        url=payload.url,
        avatar_url=payload.avatar_url,
        description=payload.description,
        sort=payload.sort,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Friend created: id=%s", row.id)
    return ok(_to_out(row).model_dump(mode="json"))


@router.patch("/{friend_id}", dependencies=write_deps)
def update_friend(
    friend_id: int,
    payload: FriendUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Apply a partial update to a friend link."""
    row = session.get(Friend, friend_id)
    if row is None:
        raise ApiError(404, "Friend not found")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field_name, value)
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Friend updated: id=%s", friend_id)
    return ok(_to_out(row).model_dump(mode="json"))


@router.delete("/{friend_id}", dependencies=write_deps)
def delete_friend(
    friend_id: int,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Delete a friend link."""
    row = session.get(Friend, friend_id)
    if row is None:
        raise ApiError(404, "Friend not found")
    session.delete(row)
    session.commit()
    logger.info("Friend deleted: id=%s", friend_id)
    return ok({"id": friend_id})


def _to_out(row: Friend) -> FriendOut:
    """Convert a friend row into the response model."""
    return FriendOut(
        id=int(row.id or 0),
        name=row.name,
        url=row.url,
        avatar_url=row.avatar_url,
        description=row.description,
        sort=row.sort,
    )
