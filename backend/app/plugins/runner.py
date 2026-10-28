"""集成实例运行器：生命周期、轮询调度、异常隔离与健康记录。"""

import logging
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db_types import utcnow
from app.domain.events import EventBus
from app.history.repository import HistoryRepository
from app.models.integration_instance import IntegrationInstance
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.contract import Integration
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


class SchedulerLike(Protocol):
    def add_job(self, func: Any, trigger: Any, **kwargs: Any) -> Any: ...

    def remove_job(self, job_id: str) -> None: ...


@dataclass
class RunningInstance:
    instance_id: int
    integration: Integration
    job_id: str


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

        context = BaseIntegrationContext(
            instance.integration,
            instance.config or {},
            self._catalog,
            self._bus,
            self._state_store,
            instance=instance.name,
        )

        integration = self._registry.create(instance.integration, context)

        await integration.setup()

        try:
            for device in await integration.discover():
                await context.register_device(device)

            job_id = f"integration:{instance.id}"

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

        except Exception:
            await integration.close()
            raise

        self._running[instance.id] = RunningInstance(
            instance_id=instance.id,
            integration=integration,
            job_id=job_id,
        )

        await self._set_health(instance.id, started=True)

        self._logger.info(
            "integration instance started: %s (%s)",
            instance.name,
            instance.integration,
        )

    async def poll_now(self, instance_id: int) -> None:
        """立即执行一次采集（调度器与测试共用）。"""

        await self._poll_job(instance_id)

    async def _poll_job(self, instance_id: int) -> None:
        running = self._running.get(instance_id)

        if running is None:
            return

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

    async def stop_instance(self, instance_id: int) -> None:
        running = self._running.pop(instance_id, None)

        if running is None:
            return

        with suppress(Exception):
            # 任务可能已因调度器关闭被移除
            self._scheduler.remove_job(running.job_id)

        try:
            await running.integration.close()

        except Exception:
            self._logger.exception(
                "integration close failed: instance=%s",
                instance_id,
            )

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

    async def _set_health(
        self,
        instance_id: int,
        *,
        started: bool = False,
        poll_ok: bool | None = None,
        error: str | None = None,
    ) -> None:
        try:
            async with self._session_factory() as db:
                await self._instances.set_health(
                    db,
                    instance_id,
                    started=started,
                    poll_ok=poll_ok,
                    error=error,
                )

        except Exception:
            self._logger.exception(
                "failed to store health for instance %s",
                instance_id,
            )
