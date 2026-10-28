from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.home_settings import HomeSettings

UPDATABLE_FIELDS = frozenset(
    {
        "home_name",
        "country",
        "province",
        "city",
        "district",
        "adcode",
        "gcj02_latitude",
        "gcj02_longitude",
        "latitude",
        "longitude",
        "timezone",
        "location_source",
    },
)
"""允许由 API 写入的字段白名单（其余字段只能由服务端维护）。"""


class SettingsRepository:
    async def get(
        self,
        db: AsyncSession,
    ) -> HomeSettings | None:
        result = await db.execute(
            select(HomeSettings).where(HomeSettings.id == 1),
        )

        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
    ) -> HomeSettings:
        settings = await self.get(db)

        if settings:
            return settings

        now = datetime.now(UTC)

        settings = HomeSettings(
            id=1,
            home_name="我的家",
            is_configured=False,
            created_at=now,
            updated_at=now,
        )

        db.add(settings)

        try:
            await db.commit()

        except IntegrityError:
            # 并发首启时另一个请求已插入，回读即可
            await db.rollback()
            settings = await self.get(db)

            if settings is None:
                raise

            return settings

        await db.refresh(settings)

        return settings

    async def update(
        self,
        db: AsyncSession,
        settings: HomeSettings,
        data: dict,
    ) -> HomeSettings:
        for key, value in data.items():
            if key not in UPDATABLE_FIELDS:
                continue

            setattr(settings, key, value)

        settings.updated_at = datetime.now(UTC)
        settings.is_configured = bool(
            settings.home_name
            and settings.latitude is not None
            and settings.longitude is not None
            and settings.timezone
        )

        await db.commit()
        await db.refresh(settings)

        return settings
