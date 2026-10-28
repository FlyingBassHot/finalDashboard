"""设备 / 实体 / 状态的只读 REST 接口。"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.db_types import utcnow
from app.models.device import Device
from app.models.entity import Entity
from app.schemas.devices import (
    DeviceResponse,
    EntityHistoryResponse,
    EntityResponse,
    EntityStateResponse,
    EntitySummary,
)
from app.services.device_service import DeviceService
from app.utils.time import ensure_utc

router = APIRouter(tags=["Devices"])

service = DeviceService()


def _device_response(
    device: Device,
    entities: list[Entity],
) -> DeviceResponse:
    response = DeviceResponse.model_validate(device)
    response.entities = [EntitySummary.model_validate(entity) for entity in entities]

    return response


@router.get(
    "/api/devices",
    response_model=list[DeviceResponse],
)
async def list_devices(
    integration: str | None = Query(default=None),
    include_entities: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    items = await service.list_devices(
        db,
        integration=integration,
        include_entities=include_entities,
    )

    return [_device_response(device, entities) for device, entities in items]


@router.get(
    "/api/devices/{device_id}",
    response_model=DeviceResponse,
)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    device, entities = await service.get_device(db, device_id)

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return _device_response(device, entities)


@router.get(
    "/api/entities",
    response_model=list[EntityResponse],
)
async def list_entities(
    device_id: str | None = Query(default=None),
    integration: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_entities(
        db,
        device_id=device_id,
        integration=integration,
    )


@router.get(
    "/api/entities/{entity_id}",
    response_model=EntityResponse,
)
async def get_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    entity = await service.get_entity(db, entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity


@router.get(
    "/api/entities/{entity_id}/state",
    response_model=EntityStateResponse,
)
async def get_entity_state(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    state = await service.get_state(db, entity_id)

    if state is None:
        raise HTTPException(status_code=404, detail="State not found")

    return EntityStateResponse(
        entity_id=state.entity_id,
        value=state.value,
        attributes=state.attributes,
        observed_at=state.observed_at,
        updated_at=state.updated_at,
    )


@router.get(
    "/api/entities/{entity_id}/history",
    response_model=list[EntityHistoryResponse],
)
async def get_entity_history(
    entity_id: str,
    start: datetime | None = Query(
        default=None,
        description="ISO 时间；缺省为 end 之前 24 小时",
    ),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    entity = await service.get_entity(db, entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    end_at = ensure_utc(end) if end is not None else utcnow()
    start_at = ensure_utc(start) if start is not None else end_at - timedelta(days=1)

    if start_at > end_at:
        raise HTTPException(
            status_code=400,
            detail="start must not be after end",
        )

    rows = await service.get_history(
        db,
        entity_id,
        start=start_at,
        end=end_at,
        limit=limit,
    )

    return [
        EntityHistoryResponse(
            entity_id=row.entity_id,
            value=row.value,
            attributes=row.attributes,
            observed_at=row.observed_at,
            recorded_at=row.recorded_at,
        )
        for row in rows
    ]
