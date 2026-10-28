"""告警 REST 接口。"""

import hmac
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerting.service import AlertService
from app.core.config import settings
from app.core.database import get_db
from app.schemas.alerts import (
    AlertmanagerPayload,
    AlertResponse,
    AlertWebhookResponse,
)

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)

service = AlertService()


def _verify_token(
    authorization: str | None,
    x_webhook_token: str | None,
) -> None:
    expected = settings.alert_webhook_token

    if not expected:
        return

    candidates = [x_webhook_token]

    if authorization and authorization.lower().startswith("bearer "):
        candidates.append(authorization[7:])

    for candidate in candidates:
        if candidate and hmac.compare_digest(candidate, expected):
            return

    raise HTTPException(
        status_code=401,
        detail="Invalid webhook token",
    )


@router.post(
    "/webhook",
    response_model=AlertWebhookResponse,
)
async def receive_webhook(
    payload: AlertmanagerPayload,
    authorization: str | None = Header(default=None),
    x_webhook_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    _verify_token(authorization, x_webhook_token)

    received = await service.ingest(db, payload)

    return AlertWebhookResponse(received=received)


@router.get(
    "",
    response_model=list[AlertResponse],
)
async def list_alerts(
    status: Literal["firing", "resolved"] | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_alerts(
        db,
        status=status,
        limit=limit,
    )


@router.get(
    "/{fingerprint}",
    response_model=AlertResponse,
)
async def get_alert(
    fingerprint: str,
    db: AsyncSession = Depends(get_db),
):
    alert = await service.get_alert(db, fingerprint)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert
