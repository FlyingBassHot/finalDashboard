from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.settings import SettingsRepository


router = APIRouter(
    prefix="/api/time",
    tags=["Time"],
)


settings_repository = SettingsRepository()

# 进程启动时刻：仅保存在内存中，用于计算服务运行时长（不落库）
STARTED_AT = datetime.now(timezone.utc)

DEFAULT_TIMEZONE = "Asia/Shanghai"


@router.get("")
async def get_server_time(
    db: AsyncSession = Depends(get_db),
):
    """服务器时间与运行时长（只读，不修改任何数据）。

    前端用 timestamp_ms 校准本机时钟偏差，
    用 timezone（家庭配置的时区）渲染时间，
    从而保证多设备显示一致且不受客户端时区设置影响。
    """

    now = datetime.now(timezone.utc)

    settings = await settings_repository.get(db)

    timezone_name = (
        settings.timezone
        if settings and settings.timezone
        else DEFAULT_TIMEZONE
    )

    return {
        "timestamp_ms": int(now.timestamp() * 1000),
        "iso_utc": now.isoformat(),
        "started_at": STARTED_AT.isoformat(),
        "timezone": timezone_name,
        "uptime_seconds": round(
            (now - STARTED_AT).total_seconds(),
            3,
        ),
    }
