"""集成实例：某个集成的一次具体配置。"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class IntegrationInstance(Base):
    __tablename__ = "integration_instances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    """实例名（全局唯一），如 "openwrt-main"。"""

    integration: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    """集成类型名，对应 IntegrationManifest.name。"""

    display_name: Mapped[str] = mapped_column(String(200), nullable=False)

    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    """集成配置（host / 用户名 / 密码等）。

    MVP 阶段明文存 SQLite，见 docs/DECISIONS.md ADR-004。
    """

    poll_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_started_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    last_poll_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
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
