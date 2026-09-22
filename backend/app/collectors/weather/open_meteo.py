import httpx


class OpenMeteoClient:

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

            "timezone": "auto",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params=params,  
            )
            response.raise_for_status()
            return response.json()

