"""设备持久化（元数据永久保存，见 D4）。"""

from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UTCDateTime, utcnow


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    """<integration>.<device_key>"""

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
    """产生该设备的集成实例名（隔离同集成的多个实例）。"""

    device_key: Mapped[str] = mapped_column(String(100), nullable=False)

    identity: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )
    """稳定硬件标识（mac:/serial:），供拓扑匹配与未来归并使用。"""

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32),
        default="unknown",
        nullable=False,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sw_version: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
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
