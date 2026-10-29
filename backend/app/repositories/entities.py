"""实体声明持久化。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.domain.entity import EntityDescriptor
from app.models.entity import Entity


class EntityRepository:
    async def upsert(
        self,
        db: AsyncSession,
        entity: EntityDescriptor,
    ) -> Entity:
        row = await db.get(Entity, entity.entity_id)

        if row is None:
            row = Entity(entity_id=entity.entity_id)
            db.add(row)

        row.integration = entity.integration
        row.instance_name = entity.instance
        row.device_id = entity.device_id
        row.entity_key = entity.key
        row.name = entity.name
        row.domain = entity.domain
        row.unit = entity.unit
        row.icon = entity.icon
        row.capabilities = sorted(
            capability.value for capability in entity.capabilities
        )
        row.attributes = dict(entity.attributes)
        row.updated_at = utcnow()

        await db.flush()

        return row

    async def get(
        self,
        db: AsyncSession,
        entity_id: str,
    ) -> Entity | None:
        return await db.get(Entity, entity_id)

    async def list(
        self,
        db: AsyncSession,
        *,
        device_id: str | None = None,
        integration: str | None = None,
        instance_name: str | None = None,
    ) -> list[Entity]:
        statement = select(Entity).order_by(Entity.entity_id)

        if device_id is not None:
            statement = statement.where(Entity.device_id == device_id)

        if integration is not None:
            statement = statement.where(Entity.integration == integration)

        if instance_name is not None:
            statement = statement.where(
                Entity.instance_name == instance_name,
            )

        result = await db.execute(statement)

        return list(result.scalars().all())

    async def delete_by_instance(
        self,
        db: AsyncSession,
        integration: str,
        instance_name: str,
    ) -> None:
        await db.execute(
            delete(Entity).where(
                Entity.integration == integration,
                Entity.instance_name == instance_name,
            ),
        )
