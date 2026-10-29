"""集成实例运行器：生命周期、轮询调度、异常隔离与健康记录。

连接（setup + discover）失败不会让实例被放弃：实例仍保留在运行列表中，
轮询任务会按配置的间隔重试连接，直到成功。这样路由器或 exporter 在
服务启动时恰好离线，恢复后无需人工重启实例。
"""

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db_types import utcnow
from app.domain.events import EventBus
from app.history.repository import HistoryRepository
from app.models.integration_instance import IntegrationInstance
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.contract import Integration
from app.plugins.manifest import CollectionMode
from app.plugins.registry import IntegrationRegistry
from app.plugins.state_store import StateStore
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)
from app.topology.repository import NeighborLinkRepository

SessionFactory = async_sessionmaker[AsyncSession]

SUBSCRIPTION_BACKOFF_START = 5.0
SUBSCRIPTION_BACKOFF_MAX = 60.0


class SchedulerLike(Protocol):
    def add_job(self, func: Any, trigger: Any, **kwargs: Any) -> Any: ...

    def remove_job(self, job_id: str) -> None: ...


@dataclass
class RunningInstance:
    instance_id: int
    name: str
    integration_name: str
    config: dict[str, Any]
    job_id: str
    collection_mode: CollectionMode = CollectionMode.POLL
    integration: Integration | None = field(default=None)
    """连接成功后才有值；为 None 表示尚未连接，下一次轮询会重试。"""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    """串行化连接过程：启动时的连接与调度器触发的轮询不能同时连接。"""

    worker: asyncio.Task[None] | None = field(default=None, repr=False)
    """订阅型集成的长驻任务；轮询型为 None。"""


class IntegrationRunner:
    def __init__(
        self,
        registry: IntegrationRegistry,
        catalog: EntityCatalog,
        bus: EventBus,
        session_factory: SessionFactory,
        state_store: StateStore,
        scheduler: SchedulerLike,
    ) -> None:
        self._registry = registry
        self._catalog = catalog
        self._bus = bus
        self._session_factory = session_factory
        self._state_store = state_store
        self._scheduler = scheduler
        self._instances = IntegrationInstanceRepository()
        self._devices = DeviceRepository()
        self._entities = EntityRepository()
        self._states = EntityStateRepository()
        self._history = HistoryRepository()
        self._neighbors = NeighborLinkRepository()
        self._running: dict[int, RunningInstance] = {}
        self._logger = logging.getLogger("app.plugins.runner")

    def is_running(self, instance_id: int) -> bool:
        return instance_id in self._running

    def running_ids(self) -> list[int]:
        return list(self._running)

    def is_connected(self, instance_id: int) -> bool:
        running = self._running.get(instance_id)

        return running is not None and running.integration is not None

    def get_integration(self, instance_name: str) -> Integration | None:
        """按实例名取当前已连接的集成；未连接或未运行为 None。"""

        for running in self._running.values():
            if running.name == instance_name:
                return running.integration

        return None

    async def start_enabled(self) -> None:
        async with self._session_factory() as db:
            instances = await self._instances.list(db, enabled=True)

        for instance in instances:
            try:
                await self.start_instance(instance)

            except Exception as exc:
                self._logger.exception(
                    "failed to start integration instance %s (%s)",
                    instance.id,
                    instance.name,
                )
                await self._set_health(
                    instance.id,
                    poll_ok=False,
                    error=f"start failed: {exc}",
                )

    async def start_instance(
        self,
        instance: IntegrationInstance,
    ) -> None:
        if instance.id in self._running:
            await self.stop_instance(instance.id)

        # 未注册的集成类型属于配置错误，直接抛给调用方
        manifest = self._registry.manifest(instance.integration)
        mode = manifest.collection_mode

        job_id = f"integration:{instance.id}"

        running = RunningInstance(
            instance_id=instance.id,
            name=instance.name,
            integration_name=instance.integration,
            config=dict(instance.config or {}),
            job_id=job_id,
            collection_mode=mode,
        )
        self._running[instance.id] = running

        if mode in {CollectionMode.POLL, CollectionMode.HYBRID}:
            self._scheduler.add_job(
                self._poll_job,
                trigger="interval",
                seconds=max(1, instance.poll_interval_seconds),
                id=job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=30,
                args=[instance.id],
                next_run_time=utcnow(),
            )

        await self._connect(running)

        if mode in {CollectionMode.SUBSCRIBE, CollectionMode.HYBRID}:
            running.worker = asyncio.create_task(
                self._subscription_loop(running),
                name=f"integration-subscribe:{instance.id}",
            )

        self._logger.info(
            "integration instance started: %s (%s, %s)",
            instance.name,
            instance.integration,
            mode.value,
        )

    async def poll_now(self, instance_id: int) -> None:
        """立即执行一次采集（调度器与测试共用）。"""

        await self._poll_job(instance_id)

    async def _connect(self, running: RunningInstance) -> bool:
        async with running.lock:
            if running.integration is not None:
                return True

            context = BaseIntegrationContext(
                running.integration_name,
                running.config,
                self._catalog,
                self._bus,
                self._state_store,
                instance=running.name,
            )

            integration: Integration | None = None

            try:
                integration = self._registry.create(
                    running.integration_name,
                    context,
                )

                await integration.setup()

                for device in await integration.discover():
                    await context.register_device(device)

            except Exception as exc:
                if integration is not None:
                    await self._close_quietly(integration, running.instance_id)

                running.integration = None

                self._logger.warning(
                    "integration connect failed: instance=%s",
                    running.instance_id,
                    exc_info=True,
                )
                await self._set_health(
                    running.instance_id,
                    poll_ok=False,
                    error=f"connect failed: {exc}",
                )

                return False

            if self._running.get(running.instance_id) is not running:
                # 连接期间实例已被停止或删除：立即释放新建的连接
                await self._close_quietly(integration, running.instance_id)

                return False

            running.integration = integration

            await self._set_health(running.instance_id, started=True)

            return True

    async def _poll_job(self, instance_id: int) -> None:
        running = self._running.get(instance_id)

        if running is None or running.collection_mode is CollectionMode.SUBSCRIBE:
            return

        if not await self._connect(running):
            return

        assert running.integration is not None

        try:
            await running.integration.poll()

        except Exception as exc:
            self._logger.warning(
                "integration poll failed: instance=%s",
                instance_id,
                exc_info=True,
            )
            await self._set_health(
                instance_id,
                poll_ok=False,
                error=str(exc),
            )
            return

        await self._set_health(instance_id, poll_ok=True)

    async def _subscription_loop(self, running: RunningInstance) -> None:
        backoff = SUBSCRIPTION_BACKOFF_START

        while self._running.get(running.instance_id) is running:
            if not await self._connect(running):
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, SUBSCRIPTION_BACKOFF_MAX)
                continue

            assert running.integration is not None

            await self._set_health(running.instance_id, connected=True)
            backoff = SUBSCRIPTION_BACKOFF_START

            try:
                await running.integration.start()

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                self._logger.warning(
                    "integration subscription failed: instance=%s",
                    running.instance_id,
                    exc_info=True,
                )
                await self._set_health(
                    running.instance_id,
                    connected=False,
                    error=f"subscribe failed: {exc}",
                )

            else:
                if self._running.get(running.instance_id) is not running:
                    return

                await self._set_health(
                    running.instance_id,
                    connected=False,
                    error="subscription ended unexpectedly",
                )

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, SUBSCRIPTION_BACKOFF_MAX)

    async def stop_instance(self, instance_id: int) -> None:
        running = self._running.pop(instance_id, None)

        if running is None:
            return

        with suppress(Exception):
            # 轮询型实例才有调度任务；订阅型没有
            self._scheduler.remove_job(running.job_id)

        if running.worker is not None:
            running.worker.cancel()

            with suppress(asyncio.CancelledError):
                await running.worker

            running.worker = None

        if running.integration is not None:
            with suppress(Exception):
                await running.integration.stop()

            await self._close_quietly(running.integration, instance_id)

        self._logger.info(
            "integration instance stopped: %s",
            instance_id,
        )

    async def stop_all(self) -> None:
        for instance_id in list(self._running):
            await self.stop_instance(instance_id)

    async def forget_instance(self, instance: IntegrationInstance) -> None:
        """删除实例时清理它产生的设备 / 实体 / 状态 / 历史 / 邻居链路。"""

        prefix = (
            ".".join(part for part in [instance.integration, instance.name] if part)
            + "."
        )

        self._catalog.remove_by_prefix(prefix)
        self._state_store.remove_by_prefix(prefix)

        async with self._session_factory() as db:
            devices = await self._devices.list(
                db,
                integration=instance.integration,
                instance_name=instance.name,
            )
            entities = await self._entities.list(
                db,
                integration=instance.integration,
                instance_name=instance.name,
            )

            entity_ids = [entity.entity_id for entity in entities]
            device_ids = [device.device_id for device in devices]

            await self._states.delete_many(db, entity_ids)
            await self._history.delete_by_entity_ids(db, entity_ids)
            await self._neighbors.delete_for_devices(db, device_ids)

            await self._entities.delete_by_instance(
                db,
                instance.integration,
                instance.name,
            )
            await self._devices.delete_by_instance(
                db,
                instance.integration,
                instance.name,
            )

            await db.commit()

        self._logger.info(
            "integration data removed: %s (%s)",
            instance.name,
            instance.integration,
        )

    async def _close_quietly(
        self,
        integration: Integration,
        instance_id: int,
    ) -> None:
        try:
            await integration.close()

        except Exception:
            self._logger.exception(
                "integration close failed: instance=%s",
                instance_id,
            )

    async def _set_health(
        self,
        instance_id: int,
        *,
        started: bool = False,
        poll_ok: bool | None = None,
        connected: bool | None = None,
        error: str | None = None,
    ) -> None:
        try:
            async with self._session_factory() as db:
                await self._instances.set_health(
                    db,
                    instance_id,
                    started=started,
                    poll_ok=poll_ok,
                    connected=connected,
                    error=error,
                )

        except Exception:
            self._logger.exception(
                "failed to store health for instance %s",
                instance_id,
            )
