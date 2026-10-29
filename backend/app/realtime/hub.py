"""进程内实时事件广播。

传输层（SSE / WebSocket）只负责订阅队列；领域事件与序列化逻辑在这里，
换通道不需要改中间层。
"""

import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from app.domain.events import DomainEvent, EventBus
from app.realtime.serializers import serialize_event


@dataclass(eq=False)
class Subscription:
    queue: asyncio.Queue[dict[str, Any]]
    types: frozenset[str] | None = None
    """为 None 表示订阅全部类型。"""


class RealtimeHub:
    def __init__(self) -> None:
        self._subscriptions: set[Subscription] = set()
        self._unsubscribe: Callable[[], None] | None = None
        self._logger = logging.getLogger("app.realtime")

    def register(self, bus: EventBus) -> None:
        self._unsubscribe = bus.subscribe(self._on_event)

    def close(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def subscribe(
        self,
        types: frozenset[str] | None = None,
    ) -> Subscription:
        subscription = Subscription(
            queue=asyncio.Queue(maxsize=100),
            types=types,
        )
        self._subscriptions.add(subscription)

        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        self._subscriptions.discard(subscription)

    async def _on_event(self, event: DomainEvent) -> None:
        payload = serialize_event(event)

        if payload is None:
            return

        await self.publish(payload)

    async def publish(self, payload: dict[str, Any]) -> None:
        for subscription in list(self._subscriptions):
            if (
                subscription.types is not None
                and payload.get("type") not in subscription.types
            ):
                continue

            try:
                subscription.queue.put_nowait(payload)

            except asyncio.QueueFull:
                # 慢消费者：丢弃最旧的一条，保证实时性
                with suppress(asyncio.QueueEmpty):
                    subscription.queue.get_nowait()

                with suppress(asyncio.QueueFull):
                    subscription.queue.put_nowait(payload)
