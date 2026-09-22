from datetime import date, datetime


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(value)


def parse_current_weather(data: dict) -> dict:
    current = data["current"]
    daily = data["daily"]
    daily_forecast = []

    for i in range(len(daily["time"])):
        each_info = {
            "forecast_date": date.fromisoformat(
                daily["time"][i]
            ),
            "weather_code": daily["weather_code"][i],
            "temperature_max": daily["temperature_2m_max"][i],
            "temperature_min": daily["temperature_2m_min"][i],
            "precipitation_sum": daily["precipitation_sum"][i],
            "precipitation_probability": daily["precipitation_probability_max"][i],
            "sunrise": _parse_datetime(daily["sunrise"][i]),
            "sunset": _parse_datetime(daily["sunset"][i]),
        }
        daily_forecast.append(each_info)

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
            "observed_at": datetime.fromisoformat(
                current["time"]
            )
        },

        "daily": daily_forecast
    }
