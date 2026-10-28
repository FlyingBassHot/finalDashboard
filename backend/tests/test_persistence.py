"""持久化订阅者测试：事件 → 数据库 → 回填。"""

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import EventBus
from app.domain.state import EntityState
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.persistence import PersistenceSubscriber
from app.plugins.state_store import StateStore
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository


async def test_registration_state_and_restore(session_factory) -> None:
    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    persistence = PersistenceSubscriber(session_factory)
    persistence.register(bus)

    context = BaseIntegrationContext(
        "test_int",
        {},
        catalog,
        bus,
        state_store,
    )

    device = await context.register_device(
        DeviceDescriptor(
            key="dev",
            name="测试设备",
            category=DeviceCategory.ROUTER,
            manufacturer="Acme",
            identity="mac:aa:bb:cc:dd:ee:ff",
        ),
    )

    entity = await context.register_entity(
        EntityDescriptor(
            key="cpu",
            name="CPU 使用率",
            domain="sensor",
            device_key="dev",
            unit="%",
            capabilities=frozenset({Capability.READONLY}),
        ),
    )

    await context.emit_state(
        entity,
        EntityState(value=42.0, attributes={"cores": 4}),
    )
    await context.emit_device_availability(device, True)

    async with session_factory() as db:
        device_row = await DeviceRepository().get(db, "test_int.dev")
        entity_row = await EntityRepository().get(db, "test_int.dev.cpu")
        state_row = await EntityStateRepository().get(
            db,
            "test_int.dev.cpu",
        )

    assert device_row is not None
    assert device_row.identity == "mac:aa:bb:cc:dd:ee:ff"
    assert device_row.available is True
    assert device_row.last_seen_at is not None

    assert entity_row is not None
    assert entity_row.capabilities == ["readonly"]
    assert entity_row.unit == "%"

    assert state_row is not None
    assert state_row.value == 42.0
    assert state_row.attributes == {"cores": 4}
    assert state_row.observed_at.tzinfo is not None

    # 模拟重启：从库回填到新的内存目录与状态表
    restored_catalog = EntityCatalog()
    restored_states = StateStore()

    await persistence.load_into(restored_catalog, restored_states)

    assert restored_catalog.find_device("test_int.dev") is not None
    assert restored_catalog.find_entity("test_int.dev.cpu") is not None

    restored_state = restored_states.get("test_int.dev.cpu")

    assert restored_state is not None
    assert restored_state.value == 42.0
    assert restored_state.attributes == {"cores": 4}

    persistence.close()


async def test_shared_state_store_tracks_old_value(session_factory) -> None:
    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    persistence = PersistenceSubscriber(session_factory)
    persistence.register(bus)

    context = BaseIntegrationContext(
        "test_int",
        {},
        catalog,
        bus,
        state_store,
    )

    entity = await context.register_entity(
        EntityDescriptor(
            key="value",
            name="值",
            domain="sensor",
        ),
    )

    await context.emit_state(entity, EntityState(value=1))
    await context.emit_state(entity, EntityState(value=2))

    current = state_store.get(entity.entity_id)

    assert current is not None
    assert current.value == 2

    persistence.close()
