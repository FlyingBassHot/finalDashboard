"""状态历史测试：变更去重、范围查询、TTL 删除。"""

from datetime import timedelta

from app.core.db_types import utcnow
from app.domain.entity import EntityDescriptor
from app.domain.events import EventBus
from app.domain.state import EntityState
from app.history.recorder import HistoryRecorder
from app.history.repository import HistoryRepository
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.state_store import StateStore


async def test_history_records_only_changes(session_factory) -> None:
    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    recorder = HistoryRecorder(session_factory)
    recorder.register(bus)

    context = BaseIntegrationContext(
        "fake_hist",
        {},
        catalog,
        bus,
        state_store,
        instance="hist",
    )

    entity = await context.register_entity(
        EntityDescriptor(
            key="value",
            name="值",
            domain="sensor",
            device_key="dev",
        ),
    )

    base = utcnow()

    await context.emit_state(
        entity,
        EntityState(value=1, observed_at=base),
    )
    # 值不变：不写历史
    await context.emit_state(
        entity,
        EntityState(value=1, observed_at=base + timedelta(seconds=10)),
    )
    # 属性变化：写历史
    await context.emit_state(
        entity,
        EntityState(
            value=1,
            attributes={"unit": "x"},
            observed_at=base + timedelta(seconds=20),
        ),
    )
    # 值变化：写历史
    await context.emit_state(
        entity,
        EntityState(value=2, observed_at=base + timedelta(seconds=30)),
    )

    async with session_factory() as db:
        rows = await HistoryRepository().query(
            db,
            entity.entity_id,
            start=base - timedelta(seconds=1),
            end=base + timedelta(seconds=60),
            limit=100,
        )

    assert [row.value for row in rows] == [1, 1, 2]
    assert rows[1].attributes == {"unit": "x"}
    assert rows[0].observed_at.tzinfo is not None

    recorder.close()


async def test_history_query_limit_and_retention(session_factory) -> None:
    bus = EventBus()
    catalog = EntityCatalog()
    state_store = StateStore()
    recorder = HistoryRecorder(session_factory)
    recorder.register(bus)

    context = BaseIntegrationContext(
        "fake_hist",
        {},
        catalog,
        bus,
        state_store,
        instance="limit",
    )

    entity = await context.register_entity(
        EntityDescriptor(
            key="value",
            name="值",
            domain="sensor",
            device_key="dev",
        ),
    )

    base = utcnow()

    for index in range(5):
        await context.emit_state(
            entity,
            EntityState(
                value=index,
                observed_at=base + timedelta(seconds=index),
            ),
        )

    repository = HistoryRepository()

    async with session_factory() as db:
        latest = await repository.query(
            db,
            entity.entity_id,
            limit=2,
        )

        assert [row.value for row in latest] == [3, 4]

        deleted = await repository.delete_before(
            db,
            base + timedelta(seconds=3),
        )
        await db.commit()

        remaining = await repository.query(
            db,
            entity.entity_id,
            limit=100,
        )

    assert deleted == 3
    assert [row.value for row in remaining] == [3, 4]

    recorder.close()
