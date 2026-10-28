"""邻居事件 → 邻居关系表。"""

import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.events import (
    DomainEvent,
    EventBus,
    NeighborReportEvent,
)
from app.topology.repository import NeighborLinkRepository

SessionFactory = async_sessionmaker[AsyncSession]


class TopologyRecorder:
    def __init__(
        self,
        session_factory: SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._repository = NeighborLinkRepository()
        self._unsubscribe: Callable[[], None] | None = None
        self._logger = logging.getLogger("app.topology.recorder")

    def register(self, bus: EventBus) -> None:
        self._unsubscribe = bus.subscribe(
            self._on_neighbor_report,
            NeighborReportEvent,
        )

    def close(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def _on_neighbor_report(self, event: DomainEvent) -> None:
        assert isinstance(event, NeighborReportEvent)

        if not event.neighbors:
            return

        async with self._session_factory() as db:
            await self._repository.upsert_many(
                db,
                event.device_id,
                event.neighbors,
                event.occurred_at,
            )
            await db.commit()
