"""设备 / 实体 / 状态的只读业务层。"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.history.repository import HistoryRepository
from app.models.device import Device
from app.models.entity import Entity
from app.models.entity_history import EntityHistory
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository


class DeviceService:
    def __init__(self) -> None:
        self.devices = DeviceRepository()
        self.entities = EntityRepository()
        self.states = EntityStateRepository()
        self.history = HistoryRepository()

    async def list_devices(
        self,
        db: AsyncSession,
        *,
        integration: str | None = None,
        include_entities: bool = True,
    ) -> list[tuple[Device, list[Entity]]]:
        devices = await self.devices.list(db, integration=integration)

        by_device: dict[str, list[Entity]] = defaultdict(list)

        if include_entities and devices:
            for entity in await self.entities.list(db):
                by_device[entity.device_id].append(entity)

        return [(device, by_device.get(device.device_id, [])) for device in devices]

    async def get_device(
        self,
        db: AsyncSession,
        device_id: str,
    ) -> tuple[Device | None, list[Entity]]:
        device = await self.devices.get(db, device_id)

        if device is None:
            return None, []

        entities = await self.entities.list(db, device_id=device_id)

        return device, entities

    async def list_entities(
        self,
        db: AsyncSession,
        *,
        device_id: str | None = None,
        integration: str | None = None,
    ) -> list[Entity]:
        return await self.entities.list(
            db,
            device_id=device_id,
            integration=integration,
        )

    async def get_entity(
        self,
        db: AsyncSession,
        entity_id: str,
    ) -> Entity | None:
        return await self.entities.get(db, entity_id)

    async def get_state(
        self,
        db: AsyncSession,
        entity_id: str,
    ):
        return await self.states.get(db, entity_id)

    async def get_history(
        self,
        db: AsyncSession,
        entity_id: str,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[EntityHistory]:
        return await self.history.query(
            db,
            entity_id,
            start=start,
            end=end,
            limit=limit,
        )
