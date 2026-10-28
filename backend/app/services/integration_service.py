"""集成实例的业务层：校验清单、落库、启停运行器。"""

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.plugins.errors import IntegrationError, UnknownIntegrationError
from app.plugins.registry import IntegrationRegistry
from app.plugins.runner import IntegrationRunner
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)
from app.schemas.integrations import (
    IntegrationInstanceCreate,
    IntegrationInstanceUpdate,
)

logger = logging.getLogger(__name__)


class IntegrationService:
    def __init__(self) -> None:
        self.repository = IntegrationInstanceRepository()

    async def list_instances(self, db: AsyncSession):
        return await self.repository.list(db)

    async def get_instance(
        self,
        db: AsyncSession,
        instance_id: int,
    ):
        instance = await self.repository.get(db, instance_id)

        if instance is None:
            raise HTTPException(
                status_code=404,
                detail="Integration instance not found",
            )

        return instance

    async def create_instance(
        self,
        db: AsyncSession,
        payload: IntegrationInstanceCreate,
        registry: IntegrationRegistry,
        runner: IntegrationRunner,
    ):
        try:
            manifest = registry.manifest(payload.integration)

        except UnknownIntegrationError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        if await self.repository.get_by_name(db, payload.name):
            raise HTTPException(
                status_code=409,
                detail=f"Instance name already exists: {payload.name}",
            )

        instance = await self.repository.create(
            db,
            name=payload.name,
            integration=payload.integration,
            display_name=payload.display_name or manifest.display_name,
            config=payload.config,
            poll_interval_seconds=(
                payload.poll_interval_seconds or manifest.default_poll_interval_seconds
            ),
            enabled=payload.enabled,
        )

        if instance.enabled:
            await self._start(runner, db, instance)

        return instance

    async def update_instance(
        self,
        db: AsyncSession,
        instance_id: int,
        payload: IntegrationInstanceUpdate,
        runner: IntegrationRunner,
    ):
        instance = await self.get_instance(db, instance_id)

        data = payload.model_dump(exclude_unset=True, exclude_none=True)

        instance = await self.repository.update(db, instance, data)

        if instance.enabled:
            await self._start(runner, db, instance)

        else:
            await runner.stop_instance(instance.id)

        return instance

    async def delete_instance(
        self,
        db: AsyncSession,
        instance_id: int,
        runner: IntegrationRunner,
    ) -> None:
        instance = await self.get_instance(db, instance_id)

        await runner.stop_instance(instance.id)
        await runner.forget_instance(instance)
        await self.repository.delete(db, instance)

    async def _start(
        self,
        runner: IntegrationRunner,
        db: AsyncSession,
        instance,
    ) -> None:
        try:
            await runner.start_instance(instance)
            await db.refresh(instance)

        except IntegrationError as exc:
            await self.repository.set_health(
                db,
                instance.id,
                poll_ok=False,
                error=f"start failed: {exc}",
            )
            await db.refresh(instance)

        except Exception as exc:
            logger.exception(
                "unexpected error starting instance %s",
                instance.id,
            )
            await self.repository.set_health(
                db,
                instance.id,
                poll_ok=False,
                error=f"start failed: {exc}",
            )
            await db.refresh(instance)
