from datetime import date, datetime

from pydantic import BaseModel


class WeatherLocation(BaseModel):
    home_name: str

    country: str | None
    province: str | None
    city: str | None
    district: str | None

    latitude: float
    longitude: float
    timezone: str


class CurrentWeatherResponse(BaseModel):
    temperature: float
    humidity: float
    apparent_temperature: float | None

    wind_speed: float | None

    weather_code: int
    is_day: bool

    observed_at: datetime


class DailyForecastResponse(BaseModel):
    date: date

    weather_code: int

    temperature_max: float
    temperature_min: float

    precipitation_probability: float | None
    precipitation_sum: float | None

    sunrise: datetime | None
    sunset: datetime | None


class WeatherResponse(BaseModel):
    location: WeatherLocation

    current: CurrentWeatherResponse

    daily: list[DailyForecastResponse]