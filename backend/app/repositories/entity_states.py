"""实体当前状态持久化。"""

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.domain.state import EntityState
from app.models.entity_state import EntityStateRecord


class EntityStateRepository:
    async def upsert(
        self,
        db: AsyncSession,
        entity_id: str,
        state: EntityState,
    ) -> EntityStateRecord:
        row = await db.get(EntityStateRecord, entity_id)

        if row is None:
            row = EntityStateRecord(entity_id=entity_id)
            db.add(row)

        row.value = state.value
        row.attributes = dict(state.attributes)
        row.observed_at = state.observed_at or utcnow()
        row.updated_at = utcnow()

        await db.flush()

        return row

    async def get(
        self,
        db: AsyncSession,
        entity_id: str,
    ) -> EntityStateRecord | None:
        return await db.get(EntityStateRecord, entity_id)

    async def list(
        self,
        db: AsyncSession,
    ) -> list[EntityStateRecord]:
        result = await db.execute(
            select(EntityStateRecord).order_by(EntityStateRecord.entity_id),
        )

        return list(result.scalars().all())

    async def delete_many(
        self,
        db: AsyncSession,
        entity_ids: Sequence[str],
    ) -> None:
        if not entity_ids:
            return

        await db.execute(
            delete(EntityStateRecord).where(
                EntityStateRecord.entity_id.in_(entity_ids),
            ),
        )
