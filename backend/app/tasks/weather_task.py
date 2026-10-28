import logging

from app.core.database import AsyncSessionLocal
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

weather_service = WeatherService()


async def update_weather_task() -> None:
    logger.info("weather update started")

    try:
        async with AsyncSessionLocal() as db:
            await weather_service.refresh(db)

    except Exception:
        logger.warning("weather update failed", exc_info=True)
