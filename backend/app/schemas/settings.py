from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationOption(BaseModel):

    adcode: str
    name: str
    level: str

    citycode: str | None = None

    center: str | None = None

    # 高德原始坐标（GCJ-02），已解析为数值
    gcj02_longitude: float | None = None
    gcj02_latitude: float | None = None

    # WGS84 坐标（供 Open-Meteo 等国际服务使用）
    longitude: float | None = None
    latitude: float | None = None

    timezone: str = "Asia/Shanghai"

    # 下级行政区（subdistrict=1 时返回，用于级联选择）
    children: list["LocationOption"] = []


LocationOption.model_rebuild()


class HomeSettingsResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    home_name: str

    country: str | None
    province: str | None
    city: str | None
    district: str | None

    adcode: str | None

    gcj02_latitude: float | None
    gcj02_longitude: float | None

    latitude: float | None
    longitude: float | None

    timezone: str | None

    location_source: str

    is_configured: bool

    created_at: datetime
    updated_at: datetime


class HomeSettingsUpdate(BaseModel):

    home_name: str

    country: str

    province: str
    city: str
    district: str | None = None

    adcode: str

    gcj02_latitude: float
    gcj02_longitude: float

    latitude: float
    longitude: float

    timezone: str

    location_source: str = "amap_district"