"""GitHub cache read and token routes."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, Depends, FastAPI, Request
from sqlmodel import Session

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.config import get_settings, save_github_token
from heartbeat.server.dependencies import get_session, require_api_key
from heartbeat.server.envelope import ApiError, ok
from heartbeat.server.schemas import GithubTokenIn, GithubTokenOut
from heartbeat.server.services.github_cache import GitHubCacheService, refresh_github_cache
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_PREFIX}/github", tags=["github"])

write_deps = [Depends(require_api_key)]

IMMEDIATE_JOB_ID = "github_cache_now"


@router.get("")
def get_github_cache(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return the cached GitHub profile payload."""
    payload = GitHubCacheService.instance().read(session)
    return ok(payload if payload is not None else {})


@router.post("/token", dependencies=write_deps)
def set_github_token(payload: GithubTokenIn, request: Request) -> dict[str, Any]:
    """Store the client-pushed GitHub PAT and queue an immediate cache refresh."""
    token = payload.token.strip()
    if not token:
        raise ApiError(400, "token must not be empty")
    login = payload.login.strip() if payload.login else None
    save_github_token(token, login or None)
    _queue_refresh(request.app)
    settings = get_settings()
    logger.info("GitHub token accepted for login=%s", settings.github_login or "unset")
    out = GithubTokenOut(configured=True, login=settings.github_login, updated_ts=current_ms())
    return ok(out.model_dump(mode="json"))


def _queue_refresh(app: FastAPI) -> None:
    """Schedule an immediate GitHub cache refresh on the running scheduler."""
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is None:
        return
    scheduler.add_job(
        refresh_github_cache,
        DateTrigger(run_date=datetime.now(timezone.utc)),
        id=IMMEDIATE_JOB_ID,
        replace_existing=True,
    )
