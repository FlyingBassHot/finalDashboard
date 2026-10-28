"""告警接收与查询业务层。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.alerting.normalize import normalize_alert
from app.alerting.repository import AlertRepository
from app.core.db_types import utcnow
from app.schemas.alerts import AlertmanagerPayload


class AlertService:
    def __init__(self) -> None:
        self.repository = AlertRepository()

    async def ingest(
        self,
        db: AsyncSession,
        payload: AlertmanagerPayload,
    ) -> int:
        received_at = utcnow()

        try:
            for alert in payload.alerts:
                await self.repository.upsert(
                    db,
                    normalize_alert(alert),
                    received_at=received_at,
                    receiver=payload.receiver,
                    group_key=payload.groupKey,
                    external_url=payload.externalURL,
                )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return len(payload.alerts)

    async def list_alerts(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        limit: int = 200,
    ):
        return await self.repository.list(
            db,
            status=status,
            limit=limit,
        )

    async def get_alert(
        self,
        db: AsyncSession,
        fingerprint: str,
    ):
        return await self.repository.get(db, fingerprint)
