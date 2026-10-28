"""实体当前状态（最新值，一行一个实体）。

历史时序不在这里：见 app/history（D4：原始采样保留 7 天）。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class EntityStateRecord(Base):
    __tablename__ = "entity_states"

    entity_id: Mapped[str] = mapped_column(String(300), primary_key=True)

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

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
