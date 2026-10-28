from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.utils.time import to_local


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
    children: list["LocationOption"] = Field(default_factory=list)


LocationOption.model_rebuild()


class HomeSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

    @field_serializer("created_at", "updated_at")
    def _serialize_local_time(self, value: datetime) -> str:
        """与天气接口保持一致：时间以家庭时区输出。"""

        return to_local(value, self.timezone).isoformat()


class HomeSettingsUpdate(BaseModel):
    home_name: str = Field(min_length=1, max_length=100)

    country: str = Field(max_length=100)
    province: str = Field(max_length=100)
    city: str = Field(max_length=100)
    district: str | None = Field(default=None, max_length=100)

    adcode: str = Field(min_length=1, max_length=20)

    gcj02_latitude: float = Field(ge=-90, le=90)
    gcj02_longitude: float = Field(ge=-180, le=180)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    timezone: str = Field(min_length=1, max_length=64)

    location_source: str = Field(
        default="amap_district",
        max_length=32,
    )

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)

        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"非法时区: {value}") from exc

        return value
