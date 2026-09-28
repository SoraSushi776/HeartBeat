"""FastAPI dependencies for database sessions and API key auth."""
from __future__ import annotations

import secrets
from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from heartbeat.protocol.models import HEADER_API_KEY
from heartbeat.server.config import get_settings
from heartbeat.server.db import create_session
from heartbeat.server.envelope import ApiError

api_key_header = APIKeyHeader(name=HEADER_API_KEY, auto_error=False)


def get_session() -> Iterator[Session]:
    """Yield a SQLModel session for the request."""
    session = create_session()
    try:
        yield session
    finally:
        session.close()


async def require_api_key(key: str | None = Depends(api_key_header)) -> str:
    """Validate X-API-Key header against the configured secret."""
    settings = get_settings()
    configured = settings.api_key
    valid = bool(configured) and key is not None and secrets.compare_digest(key, configured)
    if not valid:
        raise ApiError(401, "Invalid API Key")
    return key
