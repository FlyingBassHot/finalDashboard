from app.collectors.weather.open_meteo import OpenMeteoClient
from app.collectors.weather.parser import parse_current_weather

class WeatherCollector:
    def __init__(self):
        self.client=OpenMeteoClient()
        

    async def collect(
        self,
        latitude:float,
        longitude:float
    ) -> dict:
        raw_weather_data = await self.client.get_current_weather(latitude,longitude)
        return parse_current_weather(raw_weather_data)
        