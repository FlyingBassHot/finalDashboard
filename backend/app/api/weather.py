import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.weather import (
    CurrentWeatherResponse,
    DailyForecastResponse,
    WeatherLocation,
    WeatherResponse,
)
from app.services.weather_service import WeatherService
from app.utils.time import to_local, to_timezone

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
)

weather_service = WeatherService()


@router.post("/refresh")
async def refresh_weather(
    db: AsyncSession = Depends(get_db),
):
    try:
        return await weather_service.refresh(db)

    except httpx.HTTPError as exc:
        logger.warning("weather refresh failed", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Upstream weather service unavailable",
        ) from exc


@router.get("", response_model=WeatherResponse)
async def get_weather(
    db: AsyncSession = Depends(get_db),
):
    data = await weather_service.get_weather(db)

    settings = data["settings"]
    current = data["current"]
    daily = data["daily"]
    home_timezone = settings.timezone

    return WeatherResponse(
        location=WeatherLocation(
            home_name=settings.home_name,
            country=settings.country,
            province=settings.province,
            city=settings.city,
            district=settings.district,
            latitude=float(settings.latitude),
            longitude=float(settings.longitude),
            timezone=home_timezone or "Asia/Shanghai",
        ),
        current=CurrentWeatherResponse(
            temperature=float(current.temperature),
            humidity=float(current.humidity),
            apparent_temperature=(
                float(current.apparent_temperature)
                if current.apparent_temperature is not None
                else None
            ),
            wind_speed=(
                float(current.wind_speed) if current.wind_speed is not None else None
            ),
            weather_code=current.weather_code,
            is_day=current.is_day,
            observed_at=to_local(current.observed_at, home_timezone),
        ),
        daily=[
            DailyForecastResponse(
                date=item.forecast_date,
                weather_code=item.weather_code,
                temperature_max=float(item.temperature_max),
                temperature_min=float(item.temperature_min),
                precipitation_probability=(
                    float(item.precipitation_probability)
                    if item.precipitation_probability is not None
                    else None
                ),
                precipitation_sum=(
                    float(item.precipitation_sum)
                    if item.precipitation_sum is not None
                    else None
                ),
                sunrise=to_timezone(item.sunrise, home_timezone),
                sunset=to_timezone(item.sunset, home_timezone),
            )
            for item in daily
        ],
        fetched_at=to_timezone(current.updated_at, home_timezone),
    )
