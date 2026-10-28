from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather_daily import WeatherDaily


class WeatherDailyRepository:
    async def replace_forecast(
        self,
        db: AsyncSession,
        location_id: int,
        forecasts: list[dict],
    ):

        await db.execute(
            delete(WeatherDaily).where(WeatherDaily.location_id == location_id)
        )

        now = datetime.now(UTC)

        for forecast in forecasts:
            record = WeatherDaily(
                location_id=location_id,
                **forecast,
                updated_at=now,
            )

            db.add(record)

        await db.flush()

    async def get_all(
        self,
        db: AsyncSession,
        location_id: int,
    ):

        result = await db.execute(
            select(WeatherDaily)
            .where(WeatherDaily.location_id == location_id)
            .order_by(WeatherDaily.forecast_date)
        )

        return result.scalars().all()
