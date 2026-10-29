"""动作审计的持久化 sink。"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.plugins.action_gateway import ActionAuditRecord
from app.repositories.action_audits import ActionAuditRepository

SessionFactory = async_sessionmaker[AsyncSession]


class DatabaseAuditSink:
    """把动作审计写入 SQLite；写失败只记录日志，不阻断动作本身。"""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._repository = ActionAuditRepository()
        self._logger = logging.getLogger("app.plugins.audit")

    async def __call__(self, record: ActionAuditRecord) -> None:
        try:
            async with self._session_factory() as db:
                await self._repository.append(
                    db,
                    integration=record.integration,
                    entity_id=record.entity_id,
                    action=record.action,
                    capability=record.capability.value,
                    outcome=record.outcome,
                    message=record.message,
                    occurred_at=record.occurred_at,
                )
                await db.commit()

        except Exception:
            self._logger.exception("failed to persist action audit")
