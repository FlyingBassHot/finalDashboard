"""集成实例持久化。"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.models.integration_instance import IntegrationInstance


class IntegrationInstanceRepository:
    async def list(
        self,
        db: AsyncSession,
        enabled: bool | None = None,
    ) -> list[IntegrationInstance]:
        statement = select(IntegrationInstance).order_by(
            IntegrationInstance.id,
        )

        if enabled is not None:
            statement = statement.where(
                IntegrationInstance.enabled == enabled,
            )

        result = await db.execute(statement)

        return list(result.scalars().all())

    async def get(
        self,
        db: AsyncSession,
        instance_id: int,
    ) -> IntegrationInstance | None:
        return await db.get(IntegrationInstance, instance_id)

    async def get_by_name(
        self,
        db: AsyncSession,
        name: str,
    ) -> IntegrationInstance | None:
        result = await db.execute(
            select(IntegrationInstance).where(
                IntegrationInstance.name == name,
            ),
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        name: str,
        integration: str,
        display_name: str,
        config: dict[str, Any],
        poll_interval_seconds: int,
        enabled: bool,
    ) -> IntegrationInstance:
        instance = IntegrationInstance(
            name=name,
            integration=integration,
            display_name=display_name,
            config=config,
            poll_interval_seconds=poll_interval_seconds,
            enabled=enabled,
        )

        db.add(instance)
        await db.commit()
        await db.refresh(instance)

        return instance

    async def update(
        self,
        db: AsyncSession,
        instance: IntegrationInstance,
        data: dict[str, Any],
    ) -> IntegrationInstance:
        for key, value in data.items():
            if not hasattr(instance, key):
                continue

            setattr(instance, key, value)

        instance.updated_at = utcnow()

        await db.commit()
        await db.refresh(instance)

        return instance

    async def delete(
        self,
        db: AsyncSession,
        instance: IntegrationInstance,
    ) -> None:
        await db.delete(instance)
        await db.commit()

    async def set_health(
        self,
        db: AsyncSession,
        instance_id: int,
        *,
        started: bool = False,
        poll_ok: bool | None = None,
        error: str | None = None,
    ) -> None:
        instance = await db.get(IntegrationInstance, instance_id)

        if instance is None:
            return

        now = utcnow()

        if started:
            instance.last_started_at = now

        if poll_ok is not None:
            instance.last_poll_at = now

            if poll_ok:
                instance.last_success_at = now
                instance.last_error = None
            else:
                instance.last_error = (error or "unknown error")[:500]

        instance.updated_at = now

        await db.commit()
