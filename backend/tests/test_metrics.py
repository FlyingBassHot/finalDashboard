"""Prometheus 指标渲染测试。"""

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.export.prometheus.metrics import render_metrics
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)


async def test_render_metrics(session_factory) -> None:
    async with session_factory() as db:
        device = await DeviceRepository().upsert(
            db,
            DeviceDescriptor(
                key="main",
                name="客厅路由器",
                category=DeviceCategory.ROUTER,
                integration="openwrt",
                instance="home",
                identity="mac:aa:bb:cc:dd:ee:00",
            ),
            available=True,
        )

        numeric = await EntityRepository().upsert(
            db,
            EntityDescriptor(
                key="load",
                name='CPU "load"',
                domain="sensor",
                device_key="main",
                unit="%",
                capabilities=frozenset({Capability.READONLY}),
                integration="openwrt",
                instance="home",
            ),
        )
        boolean = await EntityRepository().upsert(
            db,
            EntityDescriptor(
                key="wan_up",
                name="WAN 连接",
                domain="binary_sensor",
                device_key="main",
                integration="openwrt",
                instance="home",
            ),
        )
        text = await EntityRepository().upsert(
            db,
            EntityDescriptor(
                key="wan_ip",
                name="WAN IP",
                domain="sensor",
                device_key="main",
                integration="openwrt",
                instance="home",
            ),
        )

        states = EntityStateRepository()
        await states.upsert(db, numeric.entity_id, EntityState(value=42.5))
        await states.upsert(db, boolean.entity_id, EntityState(value=True))
        await states.upsert(db, text.entity_id, EntityState(value="203.0.113.10"))

        instances = IntegrationInstanceRepository()
        instance = await instances.create(
            db,
            name="openwrt-home",
            integration="openwrt",
            display_name="OpenWrt",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )
        await instances.set_health(
            db,
            instance.id,
            started=True,
            poll_ok=True,
        )
        await db.commit()

        assert device.device_id == "openwrt.home.main"

    async with session_factory() as db:
        text_body = await render_metrics(db)

    assert "# TYPE homehub_device_up gauge" in text_body
    assert (
        'homehub_device_up{category="router",device_id="openwrt.home.main",'
        'instance_name="home",integration="openwrt"} 1'
    ) in text_body

    assert 'name="CPU \\"load\\""' in text_body
    assert (
        'homehub_entity_state{device_id="openwrt.home.main",'
        'domain="sensor",entity_id="openwrt.home.main.load",'
        'integration="openwrt",unit="%"} 42.5'
    ) in text_body
    assert (
        'homehub_entity_state{device_id="openwrt.home.main",'
        'domain="binary_sensor",entity_id="openwrt.home.main.wan_up",'
        'integration="openwrt",unit=""} 1'
    ) in text_body

    # 文本状态只出现在 info，不进入数值 state
    assert 'entity_id="openwrt.home.main.wan_ip"' in text_body
    assert (
        'homehub_entity_state{device_id="openwrt.home.main",'
        'domain="sensor",entity_id="openwrt.home.main.wan_ip"'
    ) not in text_body

    assert (
        'homehub_integration_healthy{instance_name="openwrt-home",'
        'integration="openwrt"} 1'
    ) in text_body
    assert (
        "homehub_integration_last_success_timestamp_seconds{"
        'instance_name="openwrt-home",integration="openwrt"}'
    ) in text_body
