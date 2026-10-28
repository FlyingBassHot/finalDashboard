"""实体声明持久化（元数据永久保存，见 D4）。"""

from datetime import datetime
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class Entity(Base):
    __tablename__ = "entities"

    entity_id: Mapped[str] = mapped_column(String(300), primary_key=True)
    """<integration>.<device_key>.<entity_key>"""

    integration: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    instance_name: Mapped[str] = mapped_column(
        String(100),
        default="",
        nullable=False,
        index=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    entity_key: Mapped[str] = mapped_column(String(100), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)

    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)

    capabilities: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # 预留给未来的实体级配置（如显示精度、告警阈值引用）
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
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
