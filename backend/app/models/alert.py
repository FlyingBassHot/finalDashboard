"""告警：Alertmanager webhook 的当前状态。"""

from datetime import datetime
from typing import Any

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class Alert(Base):
    __tablename__ = "alerts"

    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    """Alertmanager 的 fingerprint（缺失时用 labels 哈希兜底）。"""

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    """firing / resolved"""

    severity: Mapped[str] = mapped_column(
        String(32),
        default="",
        nullable=False,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    labels: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    annotations: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    last_received_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )

    generator_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    external_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    receiver: Mapped[str | None] = mapped_column(String(200), nullable=True)
    group_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    received_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
