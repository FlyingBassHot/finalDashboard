from datetime import UTC, datetime

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UTCDateTime


def _utcnow() -> datetime:
    return datetime.now(UTC)


class HomeSettings(Base):
    __tablename__ = "home_settings"

    # 整个 Home Hub 第一阶段只允许一份家庭配置
    id: Mapped[int] = mapped_column(
        primary_key=True,
        default=1,
    )

    home_name: Mapped[str] = mapped_column(
        String(100),
        default="我的家",
        nullable=False,
    )

    # -------------------------
    # 行政区信息
    # -------------------------

    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 高德行政区编码
    adcode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # -------------------------
    # 高德坐标：GCJ-02
    # 用于以后高德地图相关功能
    # -------------------------

    gcj02_latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )
    gcj02_longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    # -------------------------
    # 标准坐标：WGS84
    # 用于 Open-Meteo 等国际天气服务
    # -------------------------

    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    location_source: Mapped[str] = mapped_column(
        String(32),
        default="amap_district",
        nullable=False,
    )

    is_configured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
