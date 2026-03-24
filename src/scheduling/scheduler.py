"""
APScheduler integration for cron/interval scheduled jobs.
"""
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings

logger = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global APScheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,
            },
        )
    return _scheduler


async def start_scheduler() -> None:
    """Start the APScheduler if scheduling is enabled."""
    if not settings.SCHEDULER_ENABLED:
        logger.info("scheduler_disabled")
        return

    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler_started")


async def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("scheduler_stopped")
    _scheduler = None


def add_cron_job(
    job_id: str,
    func,
    cron_config: dict,
    args: tuple | None = None,
    kwargs: dict | None = None,
    timezone: str = "UTC",
) -> None:
    """Add a cron-triggered job to the scheduler."""
    scheduler = get_scheduler()
    trigger = CronTrigger(timezone=timezone, **cron_config)
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args,
        kwargs=kwargs,
        replace_existing=True,
    )
    logger.info("cron_job_added", job_id=job_id, config=cron_config)


def add_interval_job(
    job_id: str,
    func,
    interval_config: dict,
    args: tuple | None = None,
    kwargs: dict | None = None,
) -> None:
    """Add an interval-triggered job to the scheduler."""
    scheduler = get_scheduler()
    trigger = IntervalTrigger(**interval_config)
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args,
        kwargs=kwargs,
        replace_existing=True,
    )
    logger.info("interval_job_added", job_id=job_id, config=interval_config)


def remove_job(job_id: str) -> None:
    """Remove a job from the scheduler."""
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        logger.info("job_removed", job_id=job_id)
    except Exception:
        logger.warning("job_remove_failed", job_id=job_id)
