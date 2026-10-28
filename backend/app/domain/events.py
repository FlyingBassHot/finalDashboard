"""领域事件与进程内事件总线。

事件是北向出口的统一数据源:状态推送(实时)、
时序落库(history)、告警链路(alerting)都订阅同一总线。
"""

import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """领域事件基类。"""

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )
    source: str = ""
    """来源集成名。"""


@dataclass(frozen=True, slots=True, kw_only=True)
class StateChangedEvent(DomainEvent):
    """实体状态变更(含首次出现,old 为 None)。"""

    entity_id: str = ""
    old: EntityState | None = None
    new: EntityState | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class DeviceRegisteredEvent(DomainEvent):
    """集成注册/更新了一台设备(供持久化与北向消费)。"""

    device: DeviceDescriptor | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EntityRegisteredEvent(DomainEvent):
    """集成注册/更新了一个实体(供持久化与北向消费)。"""

    entity: EntityDescriptor | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class DeviceAvailabilityEvent(DomainEvent):
    """设备上下线。"""

    device_id: str = ""
    available: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class NeighborReportEvent(DomainEvent):
    """设备邻居表上报(供 topology 模块构建关系图)。"""

    device_id: str = ""
    neighbors: tuple[Neighbor, ...] = ()


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """进程内异步事件总线(顺序分发,handler 异常不中断)。"""

    def __init__(self) -> None:
        self._handlers: list[tuple[EventHandler, type[DomainEvent] | None]] = []

        self._logger = logging.getLogger("app.domain.events")

    def subscribe(
        self,
        handler: EventHandler,
        event_type: type[DomainEvent] | None = None,
    ) -> Callable[[], None]:
        """订阅事件,返回退订函数。

        ``event_type`` 为空时接收全部事件;否则只接收该类型
        (含子类)的事件。
        """

        entry = (handler, event_type)
        self._handlers.append(entry)

        def unsubscribe() -> None:
            with suppress(ValueError):
                self._handlers.remove(entry)

        return unsubscribe

    async def publish(
        self,
        event: DomainEvent,
    ) -> None:
        """顺序分发给所有订阅者。"""

        for handler, event_type in list(self._handlers):
            if event_type is not None and not isinstance(event, event_type):
                continue

            try:
                await handler(event)

            except Exception:
                self._logger.exception(
                    "event handler failed: %s",
                    type(event).__name__,
                )
