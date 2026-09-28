"""Database engine and schema initialization."""
from __future__ import annotations

import logging

from sqlmodel import Session, SQLModel, create_engine

from heartbeat.server.config import get_settings
from heartbeat.server.models import (
    Diary,
    Friend,
    GithubCache,
    Heartbeat,
    IpLocationCache,
    Message,
    MessageBan,
)

logger = logging.getLogger(__name__)

TABLES = (
    Heartbeat.__table__,
    Diary.__table__,
    Friend.__table__,
    Message.__table__,
    MessageBan.__table__,
    IpLocationCache.__table__,
    GithubCache.__table__,
)

_engine = None


def get_engine():
    """Return the process-wide SQLAlchemy engine singleton."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.resolved_database_url()
        _engine = create_engine(url, connect_args={"check_same_thread": False})
        logger.info("Database engine created: %s", url)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine so the next call rebuilds it."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db() -> None:
    """Create data directories and database tables."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.snapshots_dir().mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(get_engine(), tables=list(TABLES))
    logger.info("Database schema ready")


def create_session() -> Session:
    """Open a new SQLModel session."""
    return Session(get_engine())
