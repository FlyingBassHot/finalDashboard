"""领域事件与进程内事件总线。

事件是北向出口的统一数据源:状态推送(实时)、
时序落库(history)、告警链路(alerting)都订阅同一总线。
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.state import EntityState
from app.domain.topology import Neighbor


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """领域事件基类。"""

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
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
        self._handlers: list[EventHandler] = []
        self._logger = logging.getLogger(
            "app.domain.events",
        )

    def subscribe(
        self,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """订阅事件,返回退订函数。"""

        self._handlers.append(handler)

        def unsubscribe() -> None:
            try:
                self._handlers.remove(handler)
            except ValueError:
                pass

        return unsubscribe

    async def publish(
        self,
        event: DomainEvent,
    ) -> None:
        """顺序分发给所有订阅者。"""

        for handler in list(self._handlers):
            try:
                await handler(event)

            except Exception:
                self._logger.exception(
                    "event handler failed: %s",
                    type(event).__name__,
                )
