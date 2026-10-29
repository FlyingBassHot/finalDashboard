"""插件契约测试。

运行:

    uv run pytest
    # 或单独运行本文件
    uv run python tests/test_contract.py

覆盖点:
1. 清单校验(非法集成名 / 空能力 / 重复注册)
2. 只读集成链路:discover → register → emit → 事件总线收到 StateChangedEvent
3. 连续 emit 时 old 状态正确传递
4. 设备上下线事件去抖
5. 动作网关:只读集成的动作请求被能力白名单拒绝
6. 动作网关:目标实体不存在被拒绝
7. 动作网关:实体未声明能力被拒绝
8. 动作网关:跨集成的实体被拒绝
9. Wake-on-LAN 型集成成功执行并留审计
10. 只读集成声明写能力时,类创建即失败
11. 事件总线按类型订阅
12. 非 Integration 子类不能注册
"""

import sys

import pytest

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import (
    DeviceAvailabilityEvent,
    EventBus,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.plugins import (
    ActionGateway,
    ActionRequest,
    ActionResult,
    BaseIntegrationContext,
    CollectionMode,
    EntityCatalog,
    HybridIntegration,
    Integration,
    IntegrationConfigError,
    IntegrationManifest,
    IntegrationRegistry,
    PollingIntegration,
    SubscribingIntegration,
    UnsupportedActionError,
)

# --------------------------------------------
# 桩集成:第一类只读(轮询型)
# --------------------------------------------


class FakeReadOnlyIntegration(PollingIntegration):
    manifest = IntegrationManifest(
        name="fake_readonly",
        display_name="只读桩集成",
        capabilities=frozenset({Capability.READONLY}),
        supported_categories=frozenset({DeviceCategory.ROUTER}),
        default_poll_interval_seconds=30,
    )

    async def discover(self) -> list[DeviceDescriptor]:
        return [
            DeviceDescriptor(
                key="main",
                name="主路由器",
                category=DeviceCategory.ROUTER,
                manufacturer="Acme",
                model="X1",
            ),
        ]

    async def poll(self) -> None:
        entity = await self.context.register_entity(
            EntityDescriptor(
                key="cpu_load",
                name="CPU 负载",
                domain="sensor",
                device_key="main",
                unit="%",
            ),
        )

        await self.context.emit_state(entity, EntityState(value=23.5))

        await self.context.report_neighbors(
            DeviceDescriptor(key="main", name="主路由器"),
            [
                Neighbor(mac="aa:bb:cc:dd:ee:01", ip="10.0.0.2"),
                Neighbor(
                    mac="aa:bb:cc:dd:ee:02",
                    interface="wlan0",
                    is_wireless=True,
                ),
            ],
        )


# --------------------------------------------
# 桩集成:Wake-on-LAN 型(ACTION 能力)
# --------------------------------------------


class FakeWakeOnLanIntegration(Integration):
    manifest = IntegrationManifest(
        name="fake_wol",
        display_name="WoL 桩集成",
        capabilities=frozenset({Capability.ACTION}),
        supported_categories=frozenset({DeviceCategory.COMPUTER}),
        default_poll_interval_seconds=60,
    )

    async def discover(self) -> list[DeviceDescriptor]:
        return []

    async def execute_action(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        return ActionResult(
            ok=True,
            message=f"magic packet sent via {request.params.get('mac')}",
        )


class FakeOtherActionIntegration(FakeWakeOnLanIntegration):
    """同名能力的另一个集成,用于验证「实体归属」校验。"""

    manifest = IntegrationManifest(
        name="fake_action_other",
        display_name="另一个可执行动作的桩集成",
        capabilities=frozenset({Capability.ACTION}),
        supported_categories=frozenset({DeviceCategory.COMPUTER}),
        default_poll_interval_seconds=60,
    )


def _collector(target: list):
    async def collect(record) -> None:
        target.append(record)

    return collect


# --------------------------------------------
# fixtures
# --------------------------------------------


@pytest.fixture()
def catalog() -> EntityCatalog:
    return EntityCatalog()


@pytest.fixture()
def bus() -> EventBus:
    return EventBus()


@pytest.fixture()
def events(bus: EventBus) -> list:
    collected: list = []

    async def collect(event) -> None:
        collected.append(event)

    bus.subscribe(collect)

    return collected


@pytest.fixture()
def registry() -> IntegrationRegistry:
    registry = IntegrationRegistry()
    registry.register(FakeReadOnlyIntegration)
    registry.register(FakeWakeOnLanIntegration)
    registry.register(FakeOtherActionIntegration)

    return registry


# --------------------------------------------
# 测试
# --------------------------------------------


def test_manifest_validation() -> None:
    with pytest.raises(IntegrationConfigError):
        IntegrationManifest(name="BadName", display_name="非法名")

    with pytest.raises(IntegrationConfigError):
        IntegrationManifest(
            name="empty_caps",
            display_name="无能力",
            capabilities=frozenset(),
        )

    with pytest.raises(IntegrationConfigError):
        IntegrationManifest(
            name="bad_interval",
            display_name="非法间隔",
            default_poll_interval_seconds=0,
        )


def test_registry_rejects_duplicate(registry: IntegrationRegistry) -> None:
    with pytest.raises(IntegrationConfigError):
        registry.register(FakeReadOnlyIntegration)


def test_registry_rejects_non_integration() -> None:
    class NotAnIntegration:
        manifest = IntegrationManifest(
            name="not_integration",
            display_name="非法类型",
        )

    with pytest.raises(IntegrationConfigError):
        IntegrationRegistry().register(NotAnIntegration)  # type: ignore[arg-type]


def test_polling_integration_cannot_declare_control_capability() -> None:
    with pytest.raises(IntegrationConfigError):

        class BadPolling(PollingIntegration):
            manifest = IntegrationManifest(
                name="bad_polling",
                display_name="越权的只读集成",
                capabilities=frozenset(
                    {Capability.READONLY, Capability.ACTION},
                ),
            )

            async def discover(self) -> list[DeviceDescriptor]:
                return []

            async def poll(self) -> None:
                pass


async def test_readonly_pipeline(
    catalog: EntityCatalog,
    bus: EventBus,
    events: list,
    registry: IntegrationRegistry,
) -> None:
    ctx = BaseIntegrationContext(
        "fake_readonly",
        {"host": "10.0.0.1"},
        catalog,
        bus,
    )
    integration = registry.create("fake_readonly", ctx)

    devices = await integration.discover()
    assert len(devices) == 1

    device = await ctx.register_device(devices[0])
    assert device.device_id == "fake_readonly.main"
    assert catalog.find_device("fake_readonly.main") is not None

    await integration.poll()

    state_events = [event for event in events if isinstance(event, StateChangedEvent)]

    assert len(state_events) == 1
    assert state_events[0].entity_id == "fake_readonly.main.cpu_load"
    assert state_events[0].old is None
    assert state_events[0].new.value == 23.5
    assert state_events[0].source == "fake_readonly"

    entity = catalog.find_entity("fake_readonly.main.cpu_load")

    assert entity is not None
    assert entity.capabilities == frozenset({Capability.READONLY})


async def test_state_change_tracks_old(
    catalog: EntityCatalog,
    bus: EventBus,
    events: list,
    registry: IntegrationRegistry,
) -> None:
    ctx = BaseIntegrationContext("fake_readonly", {}, catalog, bus)
    integration = registry.create("fake_readonly", ctx)

    await integration.poll()
    await integration.poll()

    state_events = [event for event in events if isinstance(event, StateChangedEvent)]

    assert len(state_events) == 2
    assert state_events[1].old is not None
    assert state_events[1].old.value == 23.5


async def test_availability_debounce(
    catalog: EntityCatalog,
    bus: EventBus,
    events: list,
) -> None:
    ctx = BaseIntegrationContext("fake_readonly", {}, catalog, bus)
    router = DeviceDescriptor(key="main", name="主路由器")

    await ctx.emit_device_availability(router, False)
    await ctx.emit_device_availability(router, False)

    availability_events = [
        event for event in events if isinstance(event, DeviceAvailabilityEvent)
    ]

    assert len(availability_events) == 1
    assert availability_events[0].available is False


async def test_gateway_rejects_readonly_integration(
    catalog: EntityCatalog,
    bus: EventBus,
    registry: IntegrationRegistry,
) -> None:
    ctx = BaseIntegrationContext("fake_readonly", {}, catalog, bus)
    integration = registry.create("fake_readonly", ctx)

    await integration.poll()

    audits: list = []
    gateway = ActionGateway(catalog=catalog, audit=_collector(audits))

    with pytest.raises(UnsupportedActionError):
        await gateway.execute(
            integration,
            ActionRequest(
                entity_id="fake_readonly.main.cpu_load",
                action="wake",
                capability=Capability.ACTION,
            ),
        )

    assert audits[-1].outcome == "rejected:manifest"


async def test_gateway_rejects_missing_entity(
    catalog: EntityCatalog,
    bus: EventBus,
    registry: IntegrationRegistry,
) -> None:
    ctx = BaseIntegrationContext("fake_wol", {}, catalog, bus)
    integration = registry.create("fake_wol", ctx)

    audits: list = []
    gateway = ActionGateway(catalog=catalog, audit=_collector(audits))

    with pytest.raises(Exception) as exc_info:
        await gateway.execute(
            integration,
            ActionRequest(
                entity_id="not.exists",
                action="wake",
                capability=Capability.ACTION,
            ),
        )

    assert type(exc_info.value).__name__ == "ActionExecutionError"
    assert audits[-1].outcome == "rejected:entity-missing"


async def test_gateway_rejects_entity_without_capability(
    catalog: EntityCatalog,
    bus: EventBus,
    registry: IntegrationRegistry,
) -> None:
    wol_ctx = BaseIntegrationContext("fake_wol", {}, catalog, bus)

    await wol_ctx.register_device(
        DeviceDescriptor(key="office-pc", name="办公电脑"),
    )
    sensor = await wol_ctx.register_entity(
        EntityDescriptor(
            key="temperature",
            name="机箱温度",
            domain="sensor",
            device_key="office-pc",
        ),
    )

    wol = registry.create("fake_wol", wol_ctx)

    audits: list = []
    gateway = ActionGateway(catalog=catalog, audit=_collector(audits))

    with pytest.raises(UnsupportedActionError):
        await gateway.execute(
            wol,
            ActionRequest(
                entity_id=sensor.entity_id,
                action="wake",
                capability=Capability.ACTION,
            ),
        )

    assert audits[-1].outcome == "rejected:entity-capability"


async def test_gateway_rejects_foreign_entity(
    catalog: EntityCatalog,
    bus: EventBus,
    registry: IntegrationRegistry,
) -> None:
    owner_ctx = BaseIntegrationContext("fake_wol", {}, catalog, bus)
    await owner_ctx.register_device(
        DeviceDescriptor(key="office-pc", name="办公电脑"),
    )
    target = await owner_ctx.register_entity(
        EntityDescriptor(
            key="wol",
            name="网络唤醒",
            domain="button",
            device_key="office-pc",
            capabilities=frozenset({Capability.ACTION}),
        ),
    )

    other_ctx = BaseIntegrationContext(
        "fake_action_other",
        {},
        catalog,
        bus,
    )
    other = registry.create("fake_action_other", other_ctx)

    audits: list = []
    gateway = ActionGateway(catalog=catalog, audit=_collector(audits))

    with pytest.raises(UnsupportedActionError):
        await gateway.execute(
            other,
            ActionRequest(
                entity_id=target.entity_id,
                action="wake",
                capability=Capability.ACTION,
            ),
        )

    assert audits[-1].outcome == "rejected:entity-owner"


async def test_action_executes_and_audits(
    catalog: EntityCatalog,
    bus: EventBus,
    registry: IntegrationRegistry,
) -> None:
    ctx = BaseIntegrationContext("fake_wol", {}, catalog, bus)
    integration = registry.create("fake_wol", ctx)

    await ctx.register_device(
        DeviceDescriptor(key="office-pc", name="办公电脑"),
    )
    target = await ctx.register_entity(
        EntityDescriptor(
            key="wol",
            name="网络唤醒",
            domain="button",
            device_key="office-pc",
            capabilities=frozenset({Capability.ACTION}),
        ),
    )

    audits: list = []
    gateway = ActionGateway(catalog=catalog, audit=_collector(audits))

    result = await gateway.execute(
        integration,
        ActionRequest(
            entity_id=target.entity_id,
            action="wake",
            capability=Capability.ACTION,
            params={"mac": "aa:bb:cc:dd:ee:ff"},
        ),
    )

    assert result.ok is True
    assert audits[-1].outcome == "ok"
    assert audits[-1].integration == "fake_wol"
    assert result.message.endswith("aa:bb:cc:dd:ee:ff")


async def test_event_bus_type_filter(bus: EventBus) -> None:
    seen: list = []

    async def handler(event) -> None:
        seen.append(event)

    bus.subscribe(handler, StateChangedEvent)

    await bus.publish(DeviceAvailabilityEvent())
    assert seen == []

    await bus.publish(StateChangedEvent())
    assert len(seen) == 1


def test_collection_mode_must_match_base_class() -> None:
    with pytest.raises(IntegrationConfigError):

        class BadPolling(PollingIntegration):
            manifest = IntegrationManifest(
                name="bad_poll_mode",
                display_name="x",
                collection_mode=CollectionMode.SUBSCRIBE,
            )

            async def discover(self) -> list[DeviceDescriptor]:
                return []

            async def poll(self) -> None:
                pass

    with pytest.raises(IntegrationConfigError):

        class BadSubscribing(SubscribingIntegration):
            manifest = IntegrationManifest(
                name="bad_sub_mode",
                display_name="x",
                collection_mode=CollectionMode.POLL,
            )

            async def discover(self) -> list[DeviceDescriptor]:
                return []

            async def start(self) -> None:
                pass

    with pytest.raises(IntegrationConfigError):

        class BadHybrid(HybridIntegration):
            manifest = IntegrationManifest(
                name="bad_hybrid_mode",
                display_name="x",
                collection_mode=CollectionMode.POLL,
            )

            async def discover(self) -> list[DeviceDescriptor]:
                return []

            async def poll(self) -> None:
                pass

            async def start(self) -> None:
                pass


def test_subscribing_integration_allows_control_capability() -> None:
    class WritableSub(SubscribingIntegration):
        manifest = IntegrationManifest(
            name="writable_sub",
            display_name="可写订阅集成",
            collection_mode=CollectionMode.SUBSCRIBE,
            capabilities=frozenset({Capability.ON_OFF}),
        )

        async def discover(self) -> list[DeviceDescriptor]:
            return []

        async def start(self) -> None:
            pass

    assert WritableSub.manifest.collection_mode is CollectionMode.SUBSCRIBE


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
