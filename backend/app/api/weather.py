from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.weather import (
    CurrentWeatherResponse,
    DailyForecastResponse,
    WeatherLocation,
    WeatherResponse,
)
from app.services.weather_service import (
    WeatherService,
)


router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
)

weather_service = WeatherService()


@router.post("/refresh")
async def refresh_weather(
    db: AsyncSession = Depends(get_db),
):

    return await weather_service.refresh(db)


@router.get(
    "",
    response_model=WeatherResponse,
)
async def get_weather(
    db: AsyncSession = Depends(get_db),
):

    data = await weather_service.get_weather(db)

    settings = data["settings"]
    current = data["current"]
    daily = data["daily"]

    return WeatherResponse(

        location=WeatherLocation(
            home_name=settings.home_name,

            country=settings.country,
            province=settings.province,
            city=settings.city,
            district=settings.district,

            latitude=float(settings.latitude),
            longitude=float(settings.longitude),

            timezone=settings.timezone,
        ),

        current=CurrentWeatherResponse(
            temperature=float(
                current.temperature
            ),

            humidity=float(
                current.humidity
            ),

            apparent_temperature=(
                float(
                    current.apparent_temperature
                )
                if current.apparent_temperature
                is not None
                else None
            ),

            wind_speed=(
                float(current.wind_speed)
                if current.wind_speed is not None
                else None
            ),

            weather_code=current.weather_code,
            is_day=current.is_day,
            observed_at=current.observed_at,
        ),

        daily=[
            DailyForecastResponse(
                date=item.forecast_date,
                weather_code=item.weather_code,

                temperature_max=float(
                    item.temperature_max
                ),

                temperature_min=float(
                    item.temperature_min
                ),

                precipitation_probability=(
                    float(
                        item.precipitation_probability
                    )
                    if item.precipitation_probability
                    is not None
                    else None
                ),

                precipitation_sum=(
                    float(
                        item.precipitation_sum
                    )
                    if item.precipitation_sum
                    is not None
                    else None
                ),

                sunrise=item.sunrise,
                sunset=item.sunset,
            )
            for item in daily
        ],
    )