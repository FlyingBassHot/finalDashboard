from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import SettingsRepository


class SettingsService:
    def __init__(self) -> None:
        self.repository = SettingsRepository()

    async def get(self, db: AsyncSession):
        return await self.repository.get_or_create(db)

    async def update(self, db: AsyncSession, data: dict):
        settings = await self.repository.get_or_create(db)

        return await self.repository.update(db, settings, data)
