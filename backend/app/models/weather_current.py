from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherCurrent(Base):
    __tablename__ = "weather_current"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        default=1,
    )

    location_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    humidity: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    apparent_temperature: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    wind_speed: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    weather_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_day: Mapped[bool] = mapped_column(
        nullable=False,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )