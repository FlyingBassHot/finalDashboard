from datetime import UTC, date, datetime


def _parse_utc(value: str | None) -> datetime | None:
    """解析 Open-Meteo 时间并归一为 UTC（无时区按 UTC 解释）。"""

    if not value:
        return None

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def parse_current_weather(data: dict) -> dict:
    current = data["current"]
    daily = data["daily"]

    daily_forecast = [
        {
            "forecast_date": date.fromisoformat(daily["time"][index]),
            "weather_code": daily["weather_code"][index],
            "temperature_max": daily["temperature_2m_max"][index],
            "temperature_min": daily["temperature_2m_min"][index],
            "precipitation_sum": daily["precipitation_sum"][index],
            "precipitation_probability": (
                daily["precipitation_probability_max"][index]
            ),
            "sunrise": _parse_utc(daily["sunrise"][index]),
            "sunset": _parse_utc(daily["sunset"][index]),
        }
        for index in range(len(daily["time"]))
    ]

    return {
        "location": {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
        },
        "current": {
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "apparent_temperature": current["apparent_temperature"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "is_day": current["is_day"],
            "observed_at": _parse_utc(current["time"]),
        },
        "daily": daily_forecast,
    }
