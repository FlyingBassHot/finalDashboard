from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather_current import WeatherCurrent


class WeatherCurrentRepository:

    async def upsert(
        self,
        db: AsyncSession,
        location_id: int,
        data: dict,
    ):

        result = await db.execute(
            select(WeatherCurrent)
            .where(
                WeatherCurrent.id == 1
            )
        )

        record = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if record is None:

            record = WeatherCurrent(
                id=1,
                location_id=location_id,
                **data,
                updated_at=now,
            )

            db.add(record)

        else:

            record.location_id = location_id

            for key, value in data.items():
                setattr(record, key, value)

            record.updated_at = now

        await db.flush()

        return record

    async def get(
        self,
        db: AsyncSession,
    ):

        result = await db.execute(
            select(WeatherCurrent)
            .where(
                WeatherCurrent.id == 1
            )
        )

        return result.scalar_one_or_none()