from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.home_settings import HomeSettings


class SettingsRepository:

    async def get(
        self,
        db: AsyncSession,
    ) -> HomeSettings | None:

        result = await db.execute(
            select(HomeSettings)
            .where(HomeSettings.id == 1)
        )

        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
    ) -> HomeSettings:

        settings = await self.get(db)

        if settings:
            return settings

        now = datetime.now(timezone.utc)

        settings = HomeSettings(
            id=1,
            home_name="我的家",
            is_configured=False,
            created_at=now,
            updated_at=now,
        )

        db.add(settings)

        await db.commit()
        await db.refresh(settings)

        return settings

    async def update(
        self,
        db: AsyncSession,
        settings: HomeSettings,
        data: dict,
    ):

        for key, value in data.items():
            setattr(
                settings,
                key,
                value,
            )

        settings.updated_at = (
            datetime.now(timezone.utc)
        )

        settings.is_configured = True

        await db.commit()
        await db.refresh(settings)

        return settings

