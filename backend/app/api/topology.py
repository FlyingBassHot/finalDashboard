"""网络拓扑 REST 接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.topology import TopologyResponse
from app.topology.service import TopologyService

router = APIRouter(
    prefix="/api/topology",
    tags=["Topology"],
)

service = TopologyService()


@router.get("", response_model=TopologyResponse)
async def get_topology(
    active_within_seconds: int | None = Query(
        default=None,
        ge=60,
        le=86_400,
        description="只展示最近该窗口内上报过的邻居",
    ),
    db: AsyncSession = Depends(get_db),
):
    window = (
        active_within_seconds
        if active_within_seconds is not None
        else settings.topology_active_window_seconds
    )

    data = await service.build(
        db,
        active_within_seconds=window,
    )

    return TopologyResponse(**data)
