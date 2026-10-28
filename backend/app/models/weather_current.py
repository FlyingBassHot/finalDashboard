from datetime import UTC, datetime

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UTCDateTime


def _utcnow() -> datetime:
    return datetime.now(UTC)


class WeatherCurrent(Base):
    __tablename__ = "weather_current"

    # 第一阶段只维护一个家庭位置，固定单行
    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    location_id: Mapped[int] = mapped_column(nullable=False)

    temperature: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    humidity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    apparent_temperature: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    wind_speed: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    weather_code: Mapped[int] = mapped_column(Integer, nullable=False)
    is_day: Mapped[bool] = mapped_column(nullable=False)

    observed_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
