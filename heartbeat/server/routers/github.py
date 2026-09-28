"""GitHub cache read route."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from heartbeat.protocol.models import API_PREFIX
from heartbeat.server.dependencies import get_session
from heartbeat.server.envelope import ok
from heartbeat.server.services.github_cache import GitHubCacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_PREFIX}/github", tags=["github"])


@router.get("")
def get_github_cache(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return the cached GitHub profile payload."""
    payload = GitHubCacheService.instance().read(session)
    return ok(payload if payload is not None else {})
