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
    MessageReply,
)

logger = logging.getLogger(__name__)

TABLES = (
    Heartbeat.__table__,
    Diary.__table__,
    Friend.__table__,
    Message.__table__,
    MessageReply.__table__,
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
    """Create data directories and database tables, applying lightweight column migrations."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.snapshots_dir().mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    SQLModel.metadata.create_all(engine, tables=list(TABLES))
    _apply_column_migrations(engine)
    logger.info("Database schema ready")


def _apply_column_migrations(engine) -> None:
    """Add newly introduced columns to pre-existing SQLite tables."""
    migrations: tuple[tuple[str, str, str], ...] = (
        ("message", "ip", "TEXT DEFAULT ''"),
        ("message", "location", "TEXT DEFAULT ''"),
        ("message", "expose_ip", "INTEGER DEFAULT 0"),
    )
    with engine.connect() as connection:
        for table, column, ddl in migrations:
            _ensure_column(connection, table, column, ddl)


def _ensure_column(connection, table: str, column: str, ddl: str) -> None:
    """ALTER TABLE ADD COLUMN when the table exists but the column does not."""
    try:
        rows = connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    except Exception:
        logger.warning("Table introspection failed: %s", table)
        return
    if not rows:
        return
    names = {str(row[1]) for row in rows}
    if column in names:
        return
    connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    connection.commit()
    logger.info("Migrated column added: %s.%s", table, column)


def create_session() -> Session:
    """Open a new SQLModel session."""
    return Session(get_engine())
