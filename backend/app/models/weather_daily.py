from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherDaily(Base):
    __tablename__ = "weather_daily"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    location_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    forecast_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    weather_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    temperature_max: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    temperature_min: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    precipitation_probability: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    precipitation_sum: Mapped[float | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )

    sunrise: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    sunset: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "forecast_date",
            name="uq_weather_daily_location_date",
        ),
    )