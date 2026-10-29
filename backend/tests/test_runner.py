"""运行器测试：启动、轮询、健康记录、异常隔离。"""

import asyncio
from typing import Any

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.history.repository import HistoryRepository
from app.plugins import (
    CollectionMode,
    HybridIntegration,
    IntegrationManifest,
    IntegrationRegistry,
    PollingIntegration,
    SubscribingIntegration,
)
from app.plugins.runtime import Runtime
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)
from app.topology.repository import NeighborLinkRepository


class FakePollingIntegration(PollingIntegration):
    manifest = IntegrationManifest(
        name="fake_runner",
        display_name="运行器测试集成",
        supported_categories=frozenset({DeviceCategory.ROUTER}),
        default_poll_interval_seconds=60,
    )

    fail: bool = False
    fail_connect: bool = False

    discover_calls: int = 0

    async def discover(self) -> list[DeviceDescriptor]:
        FakePollingIntegration.discover_calls += 1
        if self.fail_connect:
            raise RuntimeError("device offline")

        return [
            DeviceDescriptor(
                key="dev",
                name="测试设备",
                category=DeviceCategory.ROUTER,
                identity="mac:aa:bb:cc:dd:ee:ff",
            ),
        ]

    async def poll(self) -> None:
        if self.fail:
            raise RuntimeError("boom")

        entity = await self.context.register_entity(
            EntityDescriptor(
                key="value",
                name="值",
                domain="sensor",
                device_key="dev",
                unit="%",
            ),
        )

        await self.context.emit_state(entity, EntityState(value=1.5))

        await self.context.report_neighbors(
            DeviceDescriptor(
                key="dev",
                name="测试设备",
                category=DeviceCategory.ROUTER,
            ),
            [
                Neighbor(
                    mac="aa:bb:cc:dd:ee:99",
                    ip="192.168.1.99",
                    hostname="neighbor",
                ),
            ],
        )


class FakeSubscribingIntegration(SubscribingIntegration):
    manifest = IntegrationManifest(
        name="fake_sub",
        display_name="订阅测试集成",
        collection_mode=CollectionMode.SUBSCRIBE,
        capabilities=frozenset({Capability.READONLY}),
        supported_categories=frozenset({DeviceCategory.ROUTER}),
    )

    instances: list = []
    fail_first: bool = False

    def __init__(self, context) -> None:
        super().__init__(context)
        self.started = asyncio.Event()
        self.stopped = False
        self.fail_this_time = type(self).fail_first
        type(self).instances.append(self)

    async def discover(self) -> list[DeviceDescriptor]:
        return [DeviceDescriptor(key="dev", name="订阅设备")]

    async def start(self) -> None:
        if self.fail_this_time:
            self.fail_this_time = False
            raise RuntimeError("subscribe boom")

        entity = await self.context.register_entity(
            EntityDescriptor(
                key="value",
                name="订阅值",
                domain="sensor",
                device_key="dev",
            ),
        )
        await self.context.emit_state(entity, EntityState(value=7))

        self.started.set()

        # 模拟长驻订阅，直到被运行器取消
        await asyncio.Event().wait()

    async def stop(self) -> None:
        self.stopped = True


class FakeHybridIntegration(HybridIntegration):
    manifest = IntegrationManifest(
        name="fake_hybrid",
        display_name="混合测试集成",
        collection_mode=CollectionMode.HYBRID,
        capabilities=frozenset({Capability.READONLY}),
        supported_categories=frozenset({DeviceCategory.ROUTER}),
    )

    poll_calls: int = 0

    def __init__(self, context) -> None:
        super().__init__(context)
        self.started = asyncio.Event()
        self.stopped = False

    async def discover(self) -> list[DeviceDescriptor]:
        return [DeviceDescriptor(key="dev", name="混合设备")]

    async def poll(self) -> None:
        type(self).poll_calls += 1

    async def start(self) -> None:
        self.started.set()
        await asyncio.Event().wait()

    async def stop(self) -> None:
        self.stopped = True


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    def add_job(self, func: Any, trigger: Any, **kwargs: Any) -> None:
        self.jobs[kwargs["id"]] = {"func": func, "kwargs": kwargs}

    def remove_job(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)


async def test_runner_starts_polls_and_records_health(session_factory) -> None:
    registry = IntegrationRegistry()
    registry.register(FakePollingIntegration)

    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-1",
            integration="fake_runner",
            display_name="测试实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    try:
        assert runtime.runner.is_running(instance.id)
        assert f"integration:{instance.id}" in scheduler.jobs
        assert runtime.catalog.find_device("fake_runner.fake-1.dev") is not None

        await runtime.runner.poll_now(instance.id)

        async with session_factory() as db:
            state = await EntityStateRepository().get(
                db,
                "fake_runner.fake-1.dev.value",
            )
            health = await IntegrationInstanceRepository().get(
                db,
                instance.id,
            )

        assert state is not None
        assert state.value == 1.5
        assert health is not None
        assert health.last_error is None
        assert health.last_success_at is not None

        # 单个实例失败不影响运行器与其他实例
        FakePollingIntegration.fail = True
        await runtime.runner.poll_now(instance.id)

        async with session_factory() as db:
            health = await IntegrationInstanceRepository().get(
                db,
                instance.id,
            )

        assert health is not None
        assert health.last_error is not None
        assert "boom" in health.last_error
        assert runtime.runner.is_running(instance.id)

    finally:
        FakePollingIntegration.fail = False
        await runtime.shutdown()

    assert not runtime.runner.is_running(instance.id)
    assert scheduler.jobs == {}


async def test_forget_instance_removes_data(session_factory) -> None:
    registry = IntegrationRegistry()
    registry.register(FakePollingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-forget",
            integration="fake_runner",
            display_name="待删除实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    try:
        await runtime.runner.poll_now(instance.id)

        assert runtime.catalog.device_count() == 1
        assert runtime.catalog.entity_count() == 1

        async with session_factory() as db:
            assert (
                len(
                    await HistoryRepository().query(
                        db, "fake_runner.fake-forget.dev.value"
                    )
                )
                == 1
            )
            assert (
                len(
                    await NeighborLinkRepository().list_for_device(
                        db, "fake_runner.fake-forget.dev"
                    )
                )
                == 1
            )

        await runtime.runner.forget_instance(instance)

        assert runtime.catalog.device_count() == 0
        assert runtime.catalog.entity_count() == 0

        async with session_factory() as db:
            assert await DeviceRepository().list(db) == []
            assert await EntityRepository().list(db) == []
            assert await EntityStateRepository().list(db) == []
            assert (
                await HistoryRepository().query(db, "fake_runner.fake-forget.dev.value")
                == []
            )
            assert (
                await NeighborLinkRepository().list_for_device(
                    db, "fake_runner.fake-forget.dev"
                )
                == []
            )

    finally:
        await runtime.shutdown()


async def test_disabled_instance_is_not_started(session_factory) -> None:
    registry = IntegrationRegistry()
    registry.register(FakePollingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-disabled",
            integration="fake_runner",
            display_name="禁用实例",
            config={},
            poll_interval_seconds=60,
            enabled=False,
        )

    await runtime.startup()

    try:
        assert not runtime.runner.is_running(instance.id)
        assert scheduler.jobs == {}

    finally:
        await runtime.shutdown()


async def test_runner_retries_connect_until_success(session_factory) -> None:
    registry = IntegrationRegistry()
    registry.register(FakePollingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-retry",
            integration="fake_runner",
            display_name="重试实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    FakePollingIntegration.fail_connect = True

    await runtime.startup()

    try:
        # 启动时设备离线：实例仍在运行列表中，但尚未连接
        assert runtime.runner.is_running(instance.id)
        assert not runtime.runner.is_connected(instance.id)
        assert f"integration:{instance.id}" in scheduler.jobs

        async with session_factory() as db:
            health = await IntegrationInstanceRepository().get(db, instance.id)

        assert health is not None
        assert health.last_error is not None
        assert "connect failed" in health.last_error

        # 设备恢复后，下一次轮询自动完成连接并采集
        FakePollingIntegration.fail_connect = False
        await runtime.runner.poll_now(instance.id)

        assert runtime.runner.is_connected(instance.id)
        assert runtime.catalog.find_device("fake_runner.fake-retry.dev") is not None

        async with session_factory() as db:
            health = await IntegrationInstanceRepository().get(db, instance.id)

        assert health is not None
        assert health.last_error is None
        assert health.last_success_at is not None

    finally:
        FakePollingIntegration.fail_connect = False
        await runtime.shutdown()


async def test_concurrent_start_and_poll_connect_once(session_factory) -> None:
    import asyncio

    registry = IntegrationRegistry()
    registry.register(FakePollingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-race",
            integration="fake_runner",
            display_name="竞态实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    FakePollingIntegration.discover_calls = 0

    # 模拟调度器在启动连接尚未完成时立即触发轮询
    await asyncio.gather(
        runtime.runner.start_instance(instance),
        runtime.runner.poll_now(instance.id),
    )

    try:
        assert FakePollingIntegration.discover_calls == 1
        assert runtime.runner.is_connected(instance.id)

        async with session_factory() as db:
            devices = await DeviceRepository().list(db, integration="fake_runner")

        assert len(devices) == 1

    finally:
        await runtime.shutdown()


async def test_subscribing_instance_runs_worker_and_stops(session_factory) -> None:
    FakeSubscribingIntegration.instances = []
    FakeSubscribingIntegration.fail_first = False

    registry = IntegrationRegistry()
    registry.register(FakeSubscribingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-sub",
            integration="fake_sub",
            display_name="订阅实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    try:
        # 订阅型不应创建轮询任务
        assert f"integration:{instance.id}" not in scheduler.jobs

        integration = runtime.runner.get_integration("fake-sub")
        assert isinstance(integration, FakeSubscribingIntegration)

        await asyncio.wait_for(integration.started.wait(), timeout=1)

        assert runtime.runner.is_connected(instance.id)
        assert "fake_sub.fake-sub.dev.value" in {
            entity.entity_id for entity in runtime.catalog.all_entities()
        }

        async with session_factory() as db:
            state = await EntityStateRepository().get(
                db,
                "fake_sub.fake-sub.dev.value",
            )
            health = await IntegrationInstanceRepository().get(db, instance.id)

        assert state is not None
        assert state.value == 7
        assert health is not None
        assert health.last_error is None
        assert health.last_success_at is not None

        await runtime.runner.stop_instance(instance.id)

        assert integration.stopped is True
        assert not runtime.runner.is_running(instance.id)

    finally:
        await runtime.shutdown()


async def test_subscription_retries_after_failure(
    session_factory,
    monkeypatch,
) -> None:
    import app.plugins.runner as runner_module

    monkeypatch.setattr(runner_module, "SUBSCRIPTION_BACKOFF_START", 0.01)
    monkeypatch.setattr(runner_module, "SUBSCRIPTION_BACKOFF_MAX", 0.02)

    FakeSubscribingIntegration.instances = []
    FakeSubscribingIntegration.fail_first = True

    registry = IntegrationRegistry()
    registry.register(FakeSubscribingIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-sub-retry",
            integration="fake_sub",
            display_name="订阅重试实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    try:
        integration = runtime.runner.get_integration("fake-sub-retry")
        assert isinstance(integration, FakeSubscribingIntegration)

        await asyncio.wait_for(integration.started.wait(), timeout=2)

        async with session_factory() as db:
            health = await IntegrationInstanceRepository().get(db, instance.id)

        assert health is not None
        assert health.last_error is None
        assert health.last_success_at is not None
        assert runtime.runner.is_connected(instance.id)

    finally:
        FakeSubscribingIntegration.fail_first = False
        await runtime.shutdown()


async def test_hybrid_instance_runs_poll_and_subscription(
    session_factory,
) -> None:
    FakeHybridIntegration.poll_calls = 0

    registry = IntegrationRegistry()
    registry.register(FakeHybridIntegration)
    scheduler = FakeScheduler()
    runtime = Runtime(session_factory, scheduler, registry=registry)

    async with session_factory() as db:
        instance = await IntegrationInstanceRepository().create(
            db,
            name="fake-hybrid",
            integration="fake_hybrid",
            display_name="混合实例",
            config={},
            poll_interval_seconds=60,
            enabled=True,
        )

    await runtime.startup()

    try:
        integration = runtime.runner.get_integration("fake-hybrid")
        assert isinstance(integration, FakeHybridIntegration)

        await asyncio.wait_for(integration.started.wait(), timeout=1)
        assert f"integration:{instance.id}" in scheduler.jobs

        await runtime.runner.poll_now(instance.id)

        assert FakeHybridIntegration.poll_calls == 1

        await runtime.runner.stop_instance(instance.id)

        assert integration.stopped is True

    finally:
        await runtime.shutdown()
