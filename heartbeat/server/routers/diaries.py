"""Diary CRUD routes."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.models import Diary
from heartbeat.server.schemas import DiaryCreate, DiaryList, DiaryOut, DiaryUpdate
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{API_PREFIX}/diaries",
    tags=["diaries"],
)

write_deps = [Depends(require_api_key)]


@router.get("")
def list_diaries(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tag: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return a paged diary list, optionally filtered by tag."""
    statement = select(Diary)
    count_statement = select(func.count()).select_from(Diary)
    if tag:
        match = Diary.tags_json.like(f'%"{tag}"%')
        statement = statement.where(match)
        count_statement = count_statement.where(match)
    total = session.exec(count_statement).one()
    rows = session.exec(
        statement.order_by(Diary.created_ts.desc()).offset(offset).limit(limit)
    ).all()
    data = DiaryList(
        items=[_to_out(row) for row in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )
    return ok(data.model_dump(mode="json"))


@router.get("/{diary_id}")
def get_diary(diary_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return one diary by id."""
    row = session.get(Diary, diary_id)
    if row is None:
        raise ApiError(404, "Diary not found")
    return ok(_to_out(row).model_dump(mode="json"))


@router.post("", dependencies=write_deps)
def create_diary(
    payload: DiaryCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Create a diary entry."""
    now_ts = current_ms()
    row = Diary(
        title=payload.title,
        content=payload.content,
        mood=payload.mood,
        tags_json=json.dumps(payload.tags),
        created_ts=now_ts,
        updated_ts=now_ts,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Diary created: id=%s", row.id)
    return ok(_to_out(row).model_dump(mode="json"))


@router.patch("/{diary_id}", dependencies=write_deps)
def update_diary(
    diary_id: int,
    payload: DiaryUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Apply a partial update to a diary entry."""
    row = session.get(Diary, diary_id)
    if row is None:
        raise ApiError(404, "Diary not found")
    updates = payload.model_dump(exclude_unset=True)
    tags = updates.pop("tags", None)
    for field_name, value in updates.items():
        setattr(row, field_name, value)
    if tags is not None:
        row.tags_json = json.dumps(tags)
    row.updated_ts = current_ms()
    session.add(row)
    session.commit()
    session.refresh(row)
    logger.info("Diary updated: id=%s", diary_id)
    return ok(_to_out(row).model_dump(mode="json"))


@router.delete("/{diary_id}", dependencies=write_deps)
def delete_diary(
    diary_id: int,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Delete a diary entry."""
    row = session.get(Diary, diary_id)
    if row is None:
        raise ApiError(404, "Diary not found")
    session.delete(row)
    session.commit()
    logger.info("Diary deleted: id=%s", diary_id)
    return ok({"id": diary_id})


def _to_out(row: Diary) -> DiaryOut:
    """Convert a diary row into the response model."""
    return DiaryOut(
        id=int(row.id or 0),
        title=row.title,
        content=row.content,
        mood=row.mood,
        tags=json.loads(row.tags_json or "[]"),
        created_ts=row.created_ts,
        updated_ts=row.updated_ts,
    )
