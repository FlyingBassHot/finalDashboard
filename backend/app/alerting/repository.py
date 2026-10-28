"""告警当前状态的数据访问层。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerting.normalize import NormalizedAlert
from app.models.alert import Alert


class AlertRepository:
    async def get(
        self,
        db: AsyncSession,
        fingerprint: str,
    ) -> Alert | None:
        return await db.get(Alert, fingerprint)

    async def list(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        limit: int = 200,
    ) -> list[Alert]:
        statement = select(Alert).order_by(Alert.last_received_at.desc()).limit(limit)

        if status is not None:
            statement = statement.where(Alert.status == status)

        result = await db.execute(statement)

        return list(result.scalars().all())

    async def upsert(
        self,
        db: AsyncSession,
        alert: NormalizedAlert,
        *,
        received_at: datetime,
        receiver: str,
        group_key: str,
        external_url: str,
    ) -> Alert:
        row = await db.get(Alert, alert.fingerprint)

        if row is None:
            row = Alert(
                fingerprint=alert.fingerprint,
                received_count=0,
                created_at=received_at,
            )
            db.add(row)

        row.name = alert.name
        row.status = alert.status
        row.severity = alert.severity
        row.summary = alert.summary
        row.description = alert.description
        row.labels = alert.labels
        row.annotations = alert.annotations
        row.starts_at = alert.starts_at
        row.ends_at = alert.ends_at
        row.generator_url = alert.generator_url
        row.receiver = receiver or None
        row.group_key = group_key or None
        row.external_url = external_url or None

        row.last_received_at = received_at
        row.received_count += 1
        row.updated_at = received_at

        if alert.status == "firing":
            row.resolved_at = None

        else:
            row.resolved_at = row.resolved_at or received_at

        await db.flush()

        return row
