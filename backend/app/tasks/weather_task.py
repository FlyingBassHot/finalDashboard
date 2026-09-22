from app.core.database import AsyncSessionLocal
from app.services.weather_service import WeatherService


weather_service = WeatherService()


async def update_weather_task():
    print("begin pull latest weather information")

    async with AsyncSessionLocal() as db:

        try:
            await weather_service.refresh(db)

            print("weather update success!")

        except Exception as e:
            print(f"weather update fail: {e}")

            await db.rollback()
