"""Prometheus 指标端点（GET /metrics）。"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.export.prometheus import CONTENT_TYPE, render_metrics

router = APIRouter(tags=["Export"])


@router.get("/metrics", summary="Prometheus metrics")
async def metrics(
    db: AsyncSession = Depends(get_db),
):
    body = await render_metrics(db)

    return Response(
        content=body,
        media_type=CONTENT_TYPE,
    )
