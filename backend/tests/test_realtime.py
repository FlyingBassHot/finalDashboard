"""实时事件 Hub 与序列化测试。"""

import asyncio

from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import EventBus
from app.domain.state import EntityState
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.state_store import StateStore
from app.realtime import RealtimeHub, serialize_event


async def test_hub_broadcasts_and_filters() -> None:
    bus = EventBus()
    hub = RealtimeHub()
    hub.register(bus)

    context = BaseIntegrationContext(
        "fake_rt",
        {},
        EntityCatalog(),
        bus,
        StateStore(),
        instance="home",
    )

    entity = await context.register_entity(
        EntityDescriptor(
            key="value",
            name="值",
            domain="sensor",
            device_key="dev",
            attributes={"precision": 1},
        ),
    )

    all_events = hub.subscribe()
    state_only = hub.subscribe(frozenset({"state_changed"}))

    await context.emit_state(entity, EntityState(value=42))

    payload = await asyncio.wait_for(all_events.queue.get(), timeout=1)
    filtered = await asyncio.wait_for(state_only.queue.get(), timeout=1)

    assert payload["type"] == "state_changed"
    assert payload["data"]["entity_id"] == "fake_rt.home.dev.value"
    assert payload["data"]["new"]["value"] == 42
    assert filtered["type"] == "state_changed"

    await context.emit_device_availability(
        DeviceDescriptor(key="dev", name="设备", category=DeviceCategory.ROUTER),
        True,
    )

    next_all = await asyncio.wait_for(all_events.queue.get(), timeout=1)

    assert next_all["type"] == "device_availability"
    assert state_only.queue.empty()

    hub.close()


def test_serializer_includes_entity_attributes() -> None:
    from app.domain.events import EntityRegisteredEvent

    payload = serialize_event(
        EntityRegisteredEvent(
            source="fake",
            entity=EntityDescriptor(
                key="load",
                name="负载",
                domain="sensor",
                device_key="dev",
                attributes={"precision": 2},
                integration="fake",
                instance="home",
            ),
        ),
    )

    assert payload is not None
    assert payload["type"] == "entity_registered"
    assert payload["data"]["entity"]["entity_id"] == "fake.home.dev.load"
    assert payload["data"]["entity"]["attributes"] == {"precision": 2}


async def test_slow_consumer_drops_oldest() -> None:
    hub = RealtimeHub()
    subscription = hub.subscribe()

    for index in range(150):
        await hub.publish({"type": "test", "index": index})

    assert subscription.queue.qsize() == 100

    first = subscription.queue.get_nowait()
    assert first["index"] == 50
