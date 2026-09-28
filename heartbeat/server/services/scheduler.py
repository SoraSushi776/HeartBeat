"""APScheduler wiring for background maintenance jobs."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from heartbeat.server.services.cleanup import run_cleanup
from heartbeat.server.services.github_cache import refresh_github_cache

logger = logging.getLogger(__name__)

GITHUB_JOB_ID = "github_cache"
CLEANUP_JOB_ID = "cleanup"
GITHUB_INTERVAL_MINUTES = 30
CLEANUP_HOUR_UTC = 4


def create_scheduler() -> BackgroundScheduler:
    """Build the UTC background scheduler with maintenance jobs."""
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_github_cache,
        IntervalTrigger(minutes=GITHUB_INTERVAL_MINUTES),
        id=GITHUB_JOB_ID,
        replace_existing=True,
    )
    scheduler.add_job(
        run_cleanup,
        CronTrigger(hour=CLEANUP_HOUR_UTC, minute=0),
        id=CLEANUP_JOB_ID,
        replace_existing=True,
    )
    logger.info("Scheduler jobs registered: %s, %s", GITHUB_JOB_ID, CLEANUP_JOB_ID)
    return scheduler
