"""动作审计：允许 / 拒绝 / 失败的全量留痕。"""

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class ActionAudit(Base):
    __tablename__ = "action_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    integration: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(300), nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    capability: Mapped[str] = mapped_column(String(32), nullable=False)

    outcome: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    """ok / rejected:<原因> / error:<原因>"""

    message: Mapped[str] = mapped_column(Text, default="", nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
