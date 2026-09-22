from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)

from app.core.config import settings
from app.tasks.weather_task import (
    update_weather_task,
)


scheduler = AsyncIOScheduler()


def start_scheduler():

    if scheduler.running:
        return

    scheduler.add_job(
        update_weather_task,

        trigger="interval",

        minutes=(
            settings.weather_update_interval_minutes
        ),

        id="weather_update",

        replace_existing=True,

        max_instances=1,

        misfire_grace_time=60,
    )

    scheduler.start()


def stop_scheduler():

    if scheduler.running:
        scheduler.shutdown(
            wait=False
        )