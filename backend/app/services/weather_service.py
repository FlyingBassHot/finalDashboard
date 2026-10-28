import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.weather.collector import WeatherCollector
from app.repositories.settings import SettingsRepository
from app.repositories.weather_current import WeatherCurrentRepository
from app.repositories.weather_daily import WeatherDailyRepository
from app.utils.time import resolve_timezone

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self) -> None:
        self.settings_repository = SettingsRepository()
        self.current_repository = WeatherCurrentRepository()
        self.daily_repository = WeatherDailyRepository()
        self.collector = WeatherCollector()

    async def refresh(
        self,
        db: AsyncSession,
    ) -> dict:
        settings = await self.settings_repository.get(db)

        if (
            not settings
            or not settings.is_configured
            or settings.latitude is None
            or settings.longitude is None
        ):
            raise HTTPException(
                status_code=409,
                detail="Home location is not configured",
            )

        weather = await self.collector.collect(
            latitude=float(settings.latitude),
            longitude=float(settings.longitude),
        )

        try:
            await self.current_repository.upsert(
                db,
                location_id=settings.id,
                data=weather["current"],
            )

            await self.daily_repository.replace_forecast(
                db,
                location_id=settings.id,
                forecasts=weather["daily"],
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        logger.info(
            "weather refreshed: lat=%s lon=%s",
            settings.latitude,
            settings.longitude,
        )

        return weather

    async def get_weather(
        self,
        db: AsyncSession,
    ) -> dict:
        settings = await self.settings_repository.get(db)

        if not settings or not settings.is_configured:
            raise HTTPException(
                status_code=409,
                detail="Home location is not configured",
            )

        current = await self.current_repository.get(db)
        daily = await self.daily_repository.get_all(db, settings.id)

        if not current:
            raise HTTPException(
                status_code=404,
                detail="Weather data not available",
            )

        # 只返回今天及以后的预报，避免调度停摆后展示过期数据
        today = (
            datetime.now(UTC)
            .astimezone(
                resolve_timezone(settings.timezone),
            )
            .date()
        )

        return {
            "settings": settings,
            "current": current,
            "daily": [item for item in daily if item.forecast_date >= today],
        }
