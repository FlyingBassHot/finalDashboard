"""告警接收与查询业务层。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.alerting.normalize import normalize_alert
from app.alerting.repository import AlertRepository
from app.core.db_types import utcnow
from app.domain.events import AlertReceivedEvent, EventBus
from app.schemas.alerts import AlertmanagerPayload


class AlertService:
    def __init__(self) -> None:
        self.repository = AlertRepository()

    async def ingest(
        self,
        db: AsyncSession,
        payload: AlertmanagerPayload,
        bus: EventBus | None = None,
    ) -> int:
        received_at = utcnow()
        normalized = [normalize_alert(alert) for alert in payload.alerts]

        try:
            for alert in normalized:
                await self.repository.upsert(
                    db,
                    alert,
                    received_at=received_at,
                    receiver=payload.receiver,
                    group_key=payload.groupKey,
                    external_url=payload.externalURL,
                )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        if bus is not None:
            for alert in normalized:
                await bus.publish(
                    AlertReceivedEvent(
                        source="alertmanager",
                        fingerprint=alert.fingerprint,
                        name=alert.name,
                        status=alert.status,
                        severity=alert.severity,
                        summary=alert.summary,
                        labels=alert.labels,
                    ),
                )

        return len(normalized)

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
