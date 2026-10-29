"""集成清单与实例的 REST 接口。"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_runtime
from app.core.database import get_db
from app.schemas.integrations import (
    IntegrationInstanceCreate,
    IntegrationInstanceResponse,
    IntegrationInstanceUpdate,
    IntegrationManifestResponse,
)
from app.services.integration_service import IntegrationService

router = APIRouter(
    prefix="/api/integrations",
    tags=["Integrations"],
)

service = IntegrationService()


@router.get(
    "/manifests",
    response_model=list[IntegrationManifestResponse],
)
async def list_manifests(request: Request):
    runtime = get_runtime(request)

    return [
        IntegrationManifestResponse.from_manifest(manifest)
        for manifest in runtime.registry.manifests()
    ]


@router.get(
    "",
    response_model=list[IntegrationInstanceResponse],
)
async def list_instances(
    db: AsyncSession = Depends(get_db),
):
    return await service.list_instances(db)


@router.get(
    "/{instance_id}",
    response_model=IntegrationInstanceResponse,
)
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_instance(db, instance_id)


@router.post(
    "",
    response_model=IntegrationInstanceResponse,
    status_code=201,
)
async def create_instance(
    payload: IntegrationInstanceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    runtime = get_runtime(request)

    return await service.create_instance(
        db,
        payload,
        runtime.registry,
        runtime.runner,
    )


@router.patch(
    "/{instance_id}",
    response_model=IntegrationInstanceResponse,
)
async def update_instance(
    instance_id: int,
    payload: IntegrationInstanceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    runtime = get_runtime(request)

    return await service.update_instance(
        db,
        instance_id,
        payload,
        runtime.runner,
    )


@router.delete(
    "/{instance_id}",
    status_code=204,
)
async def delete_instance(
    instance_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    runtime = get_runtime(request)

    await service.delete_instance(db, instance_id, runtime.runner)

    return Response(status_code=204)
