"""状态变更 → 历史表。

只记录「发生变化」的样本：值或属性不变时跳过，避免 60 秒轮询把
SQLite 写满。首次出现与每次真实变化都会留下一条记录。
"""

import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.events import (
    DomainEvent,
    EventBus,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.history.repository import HistoryRepository

SessionFactory = async_sessionmaker[AsyncSession]


def _same_state(
    old: EntityState | None,
    new: EntityState,
) -> bool:
    if old is None:
        return False

    if type(old.value) is not type(new.value):
        return False

    return old.value == new.value and dict(old.attributes) == dict(new.attributes)


class HistoryRecorder:
    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._repository = HistoryRepository()
        self._unsubscribe: Callable[[], None] | None = None
        self._logger = logging.getLogger("app.history.recorder")

    def register(self, bus: EventBus) -> None:
        self._unsubscribe = bus.subscribe(
            self._on_state_changed,
            StateChangedEvent,
        )

    def close(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def _on_state_changed(self, event: DomainEvent) -> None:
        assert isinstance(event, StateChangedEvent)

        if event.new is None or _same_state(event.old, event.new):
            return

        async with self._session_factory() as db:
            await self._repository.append(db, event.entity_id, event.new)
            await db.commit()
