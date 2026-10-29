"""事件 → 数据库 的持久化订阅者。

运行期以内存目录 / 状态表为热路径，本模块把设备的注册、实体声明、
状态变更与上下线事件落库，并在启动时把库里的数据回填到内存。
"""

import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import (
    DeviceAvailabilityEvent,
    DeviceRegisteredEvent,
    DomainEvent,
    EntityRegisteredEvent,
    EventBus,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.models.device import Device
from app.models.entity import Entity
from app.plugins.catalog import EntityCatalog
from app.plugins.state_store import StateStore
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository

SessionFactory = async_sessionmaker[AsyncSession]


def _device_from_row(row: Device) -> DeviceDescriptor:
    try:
        category = DeviceCategory(row.category)

    except ValueError:
        category = DeviceCategory.UNKNOWN

    return DeviceDescriptor(
        key=row.device_key,
        name=row.name,
        category=category,
        manufacturer=row.manufacturer,
        model=row.model,
        sw_version=row.sw_version,
        identity=row.identity,
        integration=row.integration,
        instance=row.instance_name,
    )


def _entity_from_row(row: Entity) -> EntityDescriptor:
    prefix = ".".join(part for part in [row.integration, row.instance_name] if part)
    prefix = f"{prefix}."
    device_key = (
        row.device_id[len(prefix) :] if row.device_id.startswith(prefix) else ""
    )

    capabilities = set()

    for value in row.capabilities or []:
        try:
            capabilities.add(Capability(value))

        except ValueError:
            continue

    return EntityDescriptor(
        key=row.entity_key,
        name=row.name,
        domain=row.domain,
        device_key=device_key,
        capabilities=frozenset(capabilities),
        unit=row.unit,
        icon=row.icon,
        attributes=row.attributes or {},
        integration=row.integration,
        instance=row.instance_name,
    )


class PersistenceSubscriber:
    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._devices = DeviceRepository()
        self._entities = EntityRepository()
        self._states = EntityStateRepository()
        self._logger = logging.getLogger("app.plugins.persistence")
        self._unsubscribes: list[Callable[[], None]] = []

    def register(self, bus: EventBus) -> None:
        self._unsubscribes = [
            bus.subscribe(self._on_device_registered, DeviceRegisteredEvent),
            bus.subscribe(self._on_entity_registered, EntityRegisteredEvent),
            bus.subscribe(self._on_state_changed, StateChangedEvent),
            bus.subscribe(
                self._on_availability,
                DeviceAvailabilityEvent,
            ),
        ]

    def close(self) -> None:
        for unsubscribe in self._unsubscribes:
            unsubscribe()

        self._unsubscribes.clear()

    async def load_into(
        self,
        catalog: EntityCatalog,
        state_store: StateStore,
    ) -> None:
        async with self._session_factory() as db:
            for row in await self._devices.list(db):
                catalog.add_device(_device_from_row(row))

            for row in await self._entities.list(db):
                catalog.add_entity(_entity_from_row(row))

            state_store.load(
                {
                    row.entity_id: EntityState(
                        value=row.value,
                        attributes=row.attributes,
                        observed_at=row.observed_at,
                    )
                    for row in await self._states.list(db)
                },
            )

        self._logger.info(
            "catalog restored: %s devices, %s entities",
            catalog.device_count(),
            catalog.entity_count(),
        )

    async def _on_device_registered(
        self,
        event: DomainEvent,
    ) -> None:
        assert isinstance(event, DeviceRegisteredEvent)

        if event.device is None:
            return

        async with self._session_factory() as db:
            await self._devices.upsert(db, event.device)
            await db.commit()

    async def _on_entity_registered(
        self,
        event: DomainEvent,
    ) -> None:
        assert isinstance(event, EntityRegisteredEvent)

        if event.entity is None:
            return

        async with self._session_factory() as db:
            await self._entities.upsert(db, event.entity)
            await db.commit()

    async def _on_state_changed(
        self,
        event: DomainEvent,
    ) -> None:
        assert isinstance(event, StateChangedEvent)

        if event.new is None:
            return

        async with self._session_factory() as db:
            entity = await self._entities.get(db, event.entity_id)

            if entity is None:
                self._logger.warning(
                    "state for unregistered entity ignored: %s",
                    event.entity_id,
                )
                return

            await self._states.upsert(db, event.entity_id, event.new)
            await db.commit()

    async def _on_availability(
        self,
        event: DomainEvent,
    ) -> None:
        assert isinstance(event, DeviceAvailabilityEvent)

        async with self._session_factory() as db:
            await self._devices.set_availability(
                db,
                event.device_id,
                event.available,
            )
            await db.commit()
