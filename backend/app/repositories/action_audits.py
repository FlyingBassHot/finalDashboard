"""动作审计的数据访问层。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_audit import ActionAudit


class ActionAuditRepository:
    async def append(
        self,
        db: AsyncSession,
        *,
        integration: str,
        entity_id: str,
        action: str,
        capability: str,
        outcome: str,
        message: str,
        occurred_at: datetime,
    ) -> ActionAudit:
        row = ActionAudit(
            integration=integration,
            entity_id=entity_id,
            action=action,
            capability=capability,
            outcome=outcome,
            message=message,
            occurred_at=occurred_at,
        )

        db.add(row)
        await db.flush()

        return row

    async def list(
        self,
        db: AsyncSession,
        *,
        entity_id: str | None = None,
        limit: int = 200,
    ) -> list[ActionAudit]:
        statement = (
            select(ActionAudit)
            .order_by(ActionAudit.occurred_at.desc(), ActionAudit.id.desc())
            .limit(limit)
        )

        if entity_id is not None:
            statement = statement.where(ActionAudit.entity_id == entity_id)

        result = await db.execute(statement)

        return list(result.scalars().all())
