"""运行器测试：启动、轮询、健康记录、异常隔离。"""

from typing import Any

from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.history.repository import HistoryRepository
from app.plugins import (
    IntegrationManifest,
    IntegrationRegistry,
    PollingIntegration,
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

    async def discover(self) -> list[DeviceDescriptor]:
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
