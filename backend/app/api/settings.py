from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.location.amap_district import (
    AmapDistrictClient,
)
from app.core.database import get_db
from app.schemas.settings import (
    HomeSettingsResponse,
    HomeSettingsUpdate,
    LocationOption,
)
from app.services.settings_service import (
    SettingsService,
)
from app.services.weather_service import (
    WeatherService,
)
from app.utils.coordinate import (
    gcj02_to_wgs84,
)


router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
)


settings_service = SettingsService()

weather_service = WeatherService()

amap_client = AmapDistrictClient()


@router.get(
    "/home",
    response_model=HomeSettingsResponse,
)
async def get_home_settings(
    db: AsyncSession = Depends(get_db),
):

    return await settings_service.get(db)


@router.get(
    "/locations",
    response_model=list[LocationOption],
)
async def search_locations(
    keywords: str = Query(
        ...,
        min_length=1,
        description="行政区名称或 adcode，如「河南」「410000」",
    ),
    subdistrict: int = Query(
        0,
        ge=0,
        le=2,
        description="返回下级行政区层数（级联选择时传 1）",
    ),
):

    districts = await amap_client.query(
        keywords,
        subdistrict=subdistrict,
    )

    return [
        _to_option(item)
        for item in districts
    ]


@router.put(
    "/home",
    response_model=HomeSettingsResponse,
)
async def update_home_settings(
    data: HomeSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):

    settings = await settings_service.update(
        db,
        data.model_dump(),
    )

    # 地点可能已变化，立即刷新一次天气
    # （失败不阻塞设置保存，调度器稍后会自动重试）
    try:
        await weather_service.refresh(db)

    except Exception as e:
        print(
            f"weather refresh after "
            f"settings update fail: {e}"
        )

        await db.rollback()

    return settings


def _parse_center(
    center: str | None,
) -> tuple[float | None, float | None]:
    """「经度,纬度」字符串 → (经度, 纬度)"""

    if not center:
        return None, None

    parts = center.split(",")

    if len(parts) != 2:
        return None, None

    try:
        return float(parts[0]), float(parts[1])

    except ValueError:
        return None, None


def _to_option(district: dict) -> LocationOption:
    """高德行政区原始数据 → LocationOption"""

    gcj02_lng, gcj02_lat = _parse_center(
        district.get("center")
    )

    longitude, latitude = None, None

    if gcj02_lng is not None and gcj02_lat is not None:
        longitude, latitude = gcj02_to_wgs84(
            gcj02_lng,
            gcj02_lat,
        )

    children = [
        _to_option(item)
        for item in district.get("districts") or []
    ]

    return LocationOption(
        adcode=district.get("adcode", ""),
        name=district.get("name", ""),
        level=district.get("level", ""),
        citycode=district.get("citycode") or None,
        center=district.get("center"),
        gcj02_longitude=gcj02_lng,
        gcj02_latitude=gcj02_lat,
        longitude=longitude,
        latitude=latitude,
        children=children,
    )
