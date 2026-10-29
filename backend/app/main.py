import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.integrations  # noqa: F401  注册内置集成
import app.models  # noqa: F401  确保全部 ORM 模型完成注册
from app import __version__
from app.api.actions import router as actions_router
from app.api.alerts import router as alerts_router
from app.api.devices import router as devices_router
from app.api.events import router as events_router
from app.api.integrations import router as integrations_router
from app.api.metrics import router as metrics_router
from app.api.settings import router as settings_router
from app.api.time import router as time_router
from app.api.topology import router as topology_router
from app.api.weather import router as weather_router
from app.core.config import settings as app_settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.logging import configure_logging
from app.plugins.runtime import Runtime
from app.tasks.scheduler import scheduler, start_scheduler, stop_scheduler
from app.tasks.weather_task import update_weather_task

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    start_scheduler()

    runtime = Runtime(AsyncSessionLocal, scheduler)
    app.state.runtime = runtime
    await runtime.startup()

    # 首次天气采集放到后台，网络慢或断网时不影响服务启动
    initial_refresh = asyncio.create_task(
        update_weather_task(),
        name="initial-weather-update",
    )

    yield

    if not initial_refresh.done():
        initial_refresh.cancel()

        with suppress(asyncio.CancelledError):
            await initial_refresh

    await runtime.shutdown()
    stop_scheduler()
    await engine.dispose()

    logger.info("shutdown complete")


app = FastAPI(
    title="Home Hub API",
    version=__version__,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(settings_router)
app.include_router(time_router)
app.include_router(weather_router)
app.include_router(integrations_router)
app.include_router(devices_router)
app.include_router(topology_router)
app.include_router(alerts_router)
app.include_router(actions_router)
app.include_router(events_router)
app.include_router(metrics_router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "home-hub",
    }
