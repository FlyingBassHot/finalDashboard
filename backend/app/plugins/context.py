"""IntegrationContext 的框架默认实现(进程内存态)。"""

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import (
    DeviceAvailabilityEvent,
    EventBus,
    NeighborReportEvent,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.plugins.catalog import EntityCatalog
from app.plugins.contract import IntegrationContext


class BaseIntegrationContext(IntegrationContext):
    """框架注入集成实例的默认上下文。

    职责:规范化声明(补 integration 前缀)→ 维护全局目录
    → 把状态变更 / 上下线 / 邻居上报翻译成领域事件发到总线。
    """

    def __init__(
        self,
        integration_name: str,
        config: Mapping[str, Any],
        catalog: EntityCatalog,
        bus: EventBus,
    ) -> None:
        self.integration_name = integration_name
        self._config: dict[str, Any] = dict(config)
        self._catalog = catalog
        self._bus = bus

        self._logger = logging.getLogger(
            f"app.integrations.{integration_name}",
        )

        # 该集成实例内的实体最新状态与设备在线状态(用于事件生成与去抖)
        self._last_states: dict[str, EntityState] = {}
        self._availability: dict[str, bool] = {}

    @property
    def config(self) -> Mapping[str, Any]:
        return MappingProxyType(self._config)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def register_device(
        self,
        device: DeviceDescriptor,
    ) -> DeviceDescriptor:
        normalized = self._normalize_device(device)

        self._catalog.add_device(normalized)

        return normalized

    async def register_entity(
        self,
        entity: EntityDescriptor,
    ) -> EntityDescriptor:
        normalized = self._normalize_entity(entity)

        self._catalog.add_entity(normalized)

        return normalized

    async def emit_state(
        self,
        entity: EntityDescriptor,
        state: EntityState,
    ) -> None:
        entity = self._normalize_entity(entity)

        entity_id = entity.entity_id
        old = self._last_states.get(entity_id)

        await self._bus.publish(
            StateChangedEvent(
                source=self.integration_name,
                entity_id=entity_id,
                old=old,
                new=state,
            ),
        )

        self._last_states[entity_id] = state

    async def emit_device_availability(
        self,
        device: DeviceDescriptor,
        available: bool,
    ) -> None:
        device = self._normalize_device(device)

        # 状态未变化时不重复发事件(去抖)
        if self._availability.get(device.device_id) == available:
            return

        self._availability[device.device_id] = available

        await self._bus.publish(
            DeviceAvailabilityEvent(
                source=self.integration_name,
                device_id=device.device_id,
                available=available,
            ),
        )

    async def report_neighbors(
        self,
        device: DeviceDescriptor,
        neighbors: Sequence[Neighbor],
    ) -> None:
        device = self._normalize_device(device)

        await self._bus.publish(
            NeighborReportEvent(
                source=self.integration_name,
                device_id=device.device_id,
                neighbors=tuple(neighbors),
            ),
        )

    def _normalize_entity(
        self,
        entity: EntityDescriptor,
    ) -> EntityDescriptor:
        if entity.integration == self.integration_name:
            return entity

        return dataclasses.replace(
            entity,
            integration=self.integration_name,
        )

    def _normalize_device(
        self,
        device: DeviceDescriptor,
    ) -> DeviceDescriptor:
        if device.integration == self.integration_name:
            return device

        return dataclasses.replace(
            device,
            integration=self.integration_name,
        )
