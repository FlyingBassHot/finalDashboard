"""插件契约冒烟测试 —— 无需 pytest,直接运行:

    .venv\\Scripts\\python.exe test\\test_contract.py

覆盖点:
1. 清单校验(非法集成名 / 重复注册)
2. 只读集成链路:discover → register → emit → 事件总线收到 StateChangedEvent
3. 上下线事件去抖
4. 动作网关:只读集成的动作请求被类型级拒绝(集成级白名单)
5. 动作网关:目标实体不存在被拒绝
6. 动作网关:实体未声明能力被拒绝
7. Wake-on-LAN 型集成(声明 ACTION)成功执行并留审计
8. 连续 emit 时 old 状态正确传递
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from app.domain.capability import Capability
from app.domain.device import (
    DeviceCategory,
    DeviceDescriptor,
)
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
    EntityCatalog,
    Integration,
    IntegrationConfigError,
    IntegrationManifest,
    IntegrationRegistry,
    PollingIntegration,
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

        await self.context.emit_state(
            entity,
            EntityState(value=23.5),
        )

        await self.context.report_neighbors(
            DeviceDescriptor(
                key="main",
                name="主路由器",
            ),
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
        default_poll_interval_seconds=0 + 60,
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


async def main() -> None:
    events: list = []

    bus = EventBus()

    async def collect(event) -> None:
        events.append(event)

    bus.subscribe(collect)

    catalog = EntityCatalog()
    registry = IntegrationRegistry()
    registry.register(FakeReadOnlyIntegration)
    registry.register(FakeWakeOnLanIntegration)

    # ---- 1. 清单校验 ----

    try:
        IntegrationManifest(
            name="BadName",
            display_name="非法名",
        )
        raise AssertionError("非法集成名应被拒绝")
    except IntegrationConfigError:
        pass

    try:
        IntegrationManifest(
            name="empty_caps",
            display_name="无能力",
            capabilities=frozenset(),
        )
        raise AssertionError("空能力集应被拒绝")
    except IntegrationConfigError:
        pass

    try:
        registry.register(FakeReadOnlyIntegration)
        raise AssertionError("重复注册应被拒绝")
    except IntegrationConfigError:
        pass

    # ---- 2. 只读集成完整链路 ----

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

    state_events = [
        e for e in events
        if isinstance(e, StateChangedEvent)
    ]
    assert len(state_events) == 1
    assert state_events[0].entity_id == (
        "fake_readonly.main.cpu_load"
    )
    assert state_events[0].old is None
    assert state_events[0].new.value == 23.5
    assert state_events[0].source == "fake_readonly"

    entity = catalog.find_entity(
        "fake_readonly.main.cpu_load",
    )
    assert entity is not None
    assert entity.capabilities == frozenset(
        {Capability.READONLY},
    )

    # ---- 3. 连续 emit:old 状态传递 ----

    await integration.poll()

    state_events = [
        e for e in events
        if isinstance(e, StateChangedEvent)
    ]
    assert len(state_events) == 2
    assert state_events[1].old is not None
    assert state_events[1].old.value == 23.5

    # ---- 4. 上下线去抖 ----

    router = DeviceDescriptor(
        key="main",
        name="主路由器",
    )

    await ctx.emit_device_availability(router, False)
    await ctx.emit_device_availability(router, False)

    availability_events = [
        e for e in events
        if isinstance(e, DeviceAvailabilityEvent)
    ]
    assert len(availability_events) == 1
    assert availability_events[0].available is False

    # ---- 5. 动作网关:只读集成被类型级拒绝 ----

    audits: list = []
    gateway = ActionGateway(
        catalog=catalog,
        audit=audits.append,
    )

    try:
        await gateway.execute(
            integration,
            ActionRequest(
                entity_id="fake_readonly.main.cpu_load",
                action="wake",
                capability=Capability.ACTION,
            ),
        )
        raise AssertionError("只读集成应被拒绝")
    except UnsupportedActionError:
        pass

    assert audits[-1].outcome == "rejected:manifest"

    # ---- 6. 实体不存在被拒绝 ----

    wol_ctx = BaseIntegrationContext(
        "fake_wol",
        {},
        catalog,
        bus,
    )
    wol = registry.create("fake_wol", wol_ctx)

    try:
        await gateway.execute(
            wol,
            ActionRequest(
                entity_id="not.exists",
                action="wake",
                capability=Capability.ACTION,
            ),
        )
        raise AssertionError("不存在的实体应被拒绝")
    except Exception as exc:
        assert type(exc).__name__ == "ActionExecutionError"

    assert audits[-1].outcome == "rejected:entity-missing"

    # ---- 7. 实体未声明能力被拒绝 ----

    try:
        await gateway.execute(
            wol,
            ActionRequest(
                entity_id="fake_readonly.main.cpu_load",
                action="wake",
                capability=Capability.ACTION,
            ),
        )
        raise AssertionError("未声明能力的实体应被拒绝")
    except UnsupportedActionError:
        pass

    assert audits[-1].outcome == "rejected:entity-capability"

    # ---- 8. WoL 集成成功执行 + 审计 ----

    pc = await wol_ctx.register_device(
        DeviceDescriptor(
            key="office-pc",
            name="办公电脑",
            category=DeviceCategory.COMPUTER,
        ),
    )
    target = await wol_ctx.register_entity(
        EntityDescriptor(
            key="wol",
            name="网络唤醒",
            domain="button",
            device_key="office-pc",
            capabilities=frozenset({Capability.ACTION}),
        ),
    )

    result = await gateway.execute(
        wol,
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

    print("contract smoke tests passed")


if __name__ == "__main__":
    asyncio.run(main())
