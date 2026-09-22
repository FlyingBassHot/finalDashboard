from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.settings import router as settings_router
from app.api.time import router as time_router
from app.api.weather import router as weather_router
from app.core.config import settings as app_settings
from app.core.database import Base, engine
from app.tasks.scheduler import (
    start_scheduler,
    stop_scheduler,
)
from app.tasks.weather_task import (
    update_weather_task,
)

# 确保 Model 被导入
from app.models.home_settings import HomeSettings
from app.models.weather_current import WeatherCurrent
from app.models.weather_daily import WeatherDaily


@asynccontextmanager
async def lifespan(app: FastAPI):

    # 建表
    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )

    # 启动时立即尝试一次天气更新
    await update_weather_task()

    # 启动定时器
    start_scheduler()

    yield

    # 关闭定时器
    stop_scheduler()

    # 关闭数据库
    await engine.dispose()
    print('关闭成功')

app = FastAPI(
    title="Home Hub API",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    settings_router
)

app.include_router(
    time_router
)

app.include_router(
    weather_router
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "home-hub",
    }