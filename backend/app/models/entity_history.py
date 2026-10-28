"""实体状态历史（时序，按 D4 保留 7 天）。"""

from datetime import datetime
from typing import Any

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class EntityHistory(Base):
    __tablename__ = "entity_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    entity_id: Mapped[str] = mapped_column(String(300), nullable=False)

    value: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    observed_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_entity_history_entity_observed",
            "entity_id",
            "observed_at",
        ),
    )
