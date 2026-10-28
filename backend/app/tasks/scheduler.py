import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.tasks.history_task import cleanup_history_task
from app.tasks.weather_task import update_weather_task

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        update_weather_task,
        trigger="interval",
        minutes=settings.weather_update_interval_minutes,
        id="weather_update",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    scheduler.add_job(
        cleanup_history_task,
        trigger="interval",
        minutes=settings.history_cleanup_interval_minutes,
        id="history_cleanup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    scheduler.start()

    logger.info(
        "scheduler started: weather every %s min, history cleanup every %s min",
        settings.weather_update_interval_minutes,
        settings.history_cleanup_interval_minutes,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler stopped")
