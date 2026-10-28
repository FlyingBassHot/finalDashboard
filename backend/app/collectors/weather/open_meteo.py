import httpx


class OpenMeteoClient:
    """Open-Meteo 当前天气 + 7 天预报。

    统一使用 UTC 请求，时间语义在入库前确定，
    不依赖服务端返回的本地墙钟时间。
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m,"
                "is_day"
            ),
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "sunrise,"
                "sunset"
            ),
            "forecast_days": 7,
            "timezone": "UTC",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            return response.json()
