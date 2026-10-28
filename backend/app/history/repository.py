"""状态历史的数据访问层。"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.domain.state import EntityState
from app.models.entity_history import EntityHistory


class HistoryRepository:
    async def append(
        self,
        db: AsyncSession,
        entity_id: str,
        state: EntityState,
    ) -> EntityHistory:
        row = EntityHistory(
            entity_id=entity_id,
            value=state.value,
            attributes=dict(state.attributes),
            observed_at=state.observed_at or utcnow(),
        )

        db.add(row)
        await db.flush()

        return row

    async def query(
        self,
        db: AsyncSession,
        entity_id: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
    ) -> list[EntityHistory]:
        statement = (
            select(EntityHistory)
            .where(EntityHistory.entity_id == entity_id)
            .order_by(
                EntityHistory.observed_at.desc(),
                EntityHistory.id.desc(),
            )
            .limit(limit)
        )

        if start is not None:
            statement = statement.where(EntityHistory.observed_at >= start)

        if end is not None:
            statement = statement.where(EntityHistory.observed_at <= end)

        result = await db.execute(statement)
        rows = list(result.scalars().all())
        rows.reverse()

        return rows

    async def delete_before(
        self,
        db: AsyncSession,
        cutoff: datetime,
    ) -> int:
        result = await db.execute(
            delete(EntityHistory).where(
                EntityHistory.observed_at < cutoff,
            ),
        )

        return result.rowcount or 0

    async def delete_by_entity_ids(
        self,
        db: AsyncSession,
        entity_ids: Sequence[str],
    ) -> int:
        if not entity_ids:
            return 0

        result = await db.execute(
            delete(EntityHistory).where(
                EntityHistory.entity_id.in_(entity_ids),
            ),
        )

        return result.rowcount or 0
