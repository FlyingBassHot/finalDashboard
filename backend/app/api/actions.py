"""动作执行（唯一写通道）与审计查询。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_runtime
from app.core.database import get_db
from app.plugins.contract import ActionRequest
from app.plugins.errors import (
    ActionExecutionError,
    UnsupportedActionError,
)
from app.repositories.action_audits import ActionAuditRepository
from app.schemas.actions import (
    ActionAuditResponse,
    ActionExecuteRequest,
    ActionExecuteResponse,
)
from app.services.device_service import DeviceService

router = APIRouter(tags=["Actions"])

service = DeviceService()
audits = ActionAuditRepository()


@router.post(
    "/api/entities/{entity_id}/actions",
    response_model=ActionExecuteResponse,
)
async def execute_action(
    entity_id: str,
    payload: ActionExecuteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    entity = await service.get_entity(db, entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    runtime = get_runtime(request)
    integration = runtime.runner.get_integration(entity.instance_name)

    if integration is None:
        raise HTTPException(
            status_code=409,
            detail="Integration instance is not running",
        )

    try:
        result = await runtime.action_gateway.execute(
            integration,
            ActionRequest(
                entity_id=entity.entity_id,
                action=payload.action,
                capability=payload.capability,
                params=payload.params,
            ),
        )

    except UnsupportedActionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    except ActionExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ActionExecuteResponse(
        ok=result.ok,
        message=result.message,
    )


@router.get(
    "/api/action-audits",
    response_model=list[ActionAuditResponse],
)
async def list_action_audits(
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    return await audits.list(
        db,
        entity_id=entity_id,
        limit=limit,
    )
