from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.weather.collector import (
    WeatherCollector,
)
from app.repositories.settings import (
    SettingsRepository,
)
from app.repositories.weather_current import (
    WeatherCurrentRepository,
)
from app.repositories.weather_daily import (
    WeatherDailyRepository,
)


class WeatherService:

    def __init__(self):

        self.settings_repository = (
            SettingsRepository()
        )

        self.current_repository = (
            WeatherCurrentRepository()
        )

        self.daily_repository = (
            WeatherDailyRepository()
        )

        self.collector = WeatherCollector()

    async def refresh(
        self,
        db: AsyncSession,
    ):

        settings = (
            await self.settings_repository.get(db)
        )

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

        return weather

    async def get_weather(
        self,
        db: AsyncSession,
    ):

        settings = (
            await self.settings_repository.get(db)
        )

        if not settings or not settings.is_configured:
            raise HTTPException(
                status_code=409,
                detail="Home location is not configured",
            )

        current = (
            await self.current_repository.get(db)
        )

        daily = await self.daily_repository.get_all(
            db,
            settings.id,
        )

        if not current:
            raise HTTPException(
                status_code=404,
                detail="Weather data not available",
            )

        return {
            "settings": settings,
            "current": current,
            "daily": daily,
        }