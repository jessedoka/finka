"""In-container daily net-worth snapshot scheduler.

A dependency-free asyncio loop: sleep until the next configured HH:MM, record a
snapshot for the dev user, repeat. Started/stopped from the FastAPI lifespan.

This is the LOCAL stand-in for what becomes an AWS EventBridge schedule -> Lambda
later (roadmap Milestone 3/6). It records the same snapshot the manual
`scripts/snapshot.py` does — just on a timer while the container is up.

Assumes the single dev user (auth is stubbed in Phase 0). When real auth lands,
iterate over users instead.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from config import settings
from database import async_session
from query_selectors.user_selector import UserSelector
from services.net_worth_service import NetWorthService

logger = logging.getLogger(__name__)

DEV_USER_SUB = "dev-user-001"


def _seconds_until(hh_mm: str) -> float:
    """Seconds from now until the next occurrence of HH:MM (local time)."""
    hour, minute = (int(x) for x in hh_mm.split(":"))
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def _run_once() -> None:
    async with async_session() as db:
        user = await db.scalar(UserSelector(DEV_USER_SUB).records)
        if user is None:
            logger.warning("Snapshot scheduler: no dev user %r; skipping.", DEV_USER_SUB)
            return
        snapshot = await NetWorthService(db).record_snapshot(user.id)
        logger.info(
            "Snapshot recorded for %s: net_worth=%s", snapshot.snapshot_date, snapshot.net_worth
        )


async def _loop() -> None:
    logger.info("Snapshot scheduler started; daily at %s.", settings.snapshot_time)
    while True:
        delay = _seconds_until(settings.snapshot_time)
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logger.info("Snapshot scheduler stopped.")
            raise
        try:
            await _run_once()
        except Exception:  # never let one bad run kill the loop
            logger.exception("Snapshot scheduler run failed; will retry tomorrow.")


def start(app) -> None:
    """Launch the loop as a background task stored on app.state."""
    if not settings.snapshot_scheduler_enabled:
        logger.info("Snapshot scheduler disabled (SNAPSHOT_SCHEDULER_ENABLED=false).")
        return
    app.state.snapshot_task = asyncio.create_task(_loop())


async def stop(app) -> None:
    task = getattr(app.state, "snapshot_task", None)
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
