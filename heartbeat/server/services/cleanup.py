"""Expired heartbeat and screenshot cleanup service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session, select

from heartbeat.server.config import get_settings
from heartbeat.server.db import create_session
from heartbeat.server.models import Heartbeat
from heartbeat.server.timeutil import current_ms

logger = logging.getLogger(__name__)

DAY_MS = 86_400_000


class CleanupService:
    """Delete aged heartbeats and stale screenshot history files."""

    _instance: CleanupService | None = None

    @classmethod
    def instance(cls) -> CleanupService:
        """Return the process-wide cleanup service singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def run(self) -> None:
        """Execute one cleanup pass over heartbeats and screenshots."""
        settings = get_settings()
        cutoff_ts = current_ms() - settings.heartbeat_retention_days * DAY_MS
        session = create_session()
        try:
            removed = self._delete_heartbeats(session, cutoff_ts)
        finally:
            session.close()
        pruned = self._prune_screenshots()
        logger.info("Cleanup finished: heartbeats=%d screenshots=%d", removed, pruned)

    def _delete_heartbeats(self, session: Session, cutoff_ts: int) -> int:
        """Delete heartbeat rows older than cutoff_ts."""
        statement = select(Heartbeat).where(Heartbeat.ts < cutoff_ts)
        rows = session.exec(statement).all()
        for row in rows:
            session.delete(row)
        session.commit()
        return len(rows)

    def _prune_screenshots(self) -> int:
        """Delete history screenshots outside the retention window."""
        settings = get_settings()
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=settings.screenshot_retention_days)
        removed = 0
        directory = settings.snapshots_dir()
        if not directory.is_dir():
            return 0
        for path in directory.iterdir():
            if self._should_prune(path, cutoff):
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    def _should_prune(self, path: Path, cutoff: datetime) -> bool:
        """Return True when a snapshot file is stale history or orphaned meta."""
        name = path.name
        if not path.is_file():
            return False
        if name.endswith(".meta.json"):
            latest_webp = path.with_name(name.replace(".meta.json", ".webp"))
            return not latest_webp.exists()
        if "latest" in name:
            return False
        if not name.endswith(".webp"):
            return False
        stamp = path.stem.rsplit("-", 1)[-1]
        try:
            day = datetime.strptime(stamp, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        return day < cutoff


def run_cleanup() -> None:
    """Scheduled job entry that runs one cleanup pass."""
    CleanupService.instance().run()
