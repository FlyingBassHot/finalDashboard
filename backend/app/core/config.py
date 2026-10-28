from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
"""backend/ 目录（本文件位于 backend/app/core/config.py）。"""

DEFAULT_DATABASE_URL = (
    f"sqlite+aiosqlite:///{(BACKEND_DIR / 'data' / 'home_hub.db').as_posix()}"
)
"""默认库路径按 backend/ 解析，避免从不同工作目录启动时落到不同文件。"""

_SQLITE_PREFIX = "sqlite+aiosqlite:///"


class Settings(BaseSettings):
    app_name: str = "Home Hub"

    database_url: str = DEFAULT_DATABASE_URL

    weather_update_interval_minutes: int = Field(
        default=10,
        ge=1,
    )

    history_retention_days: int = Field(
        default=7,
        ge=1,
    )
    """状态历史 / 邻居关系保留天数（D4）。"""

    history_cleanup_interval_minutes: int = Field(
        default=360,
        ge=5,
    )

    topology_active_window_seconds: int = Field(
        default=600,
        ge=60,
    )
    """拓扑只展示最近该窗口内上报过的邻居。"""

    alert_webhook_token: str = ""
    """Alertmanager webhook 共享令牌。为空表示不校验（仅建议内网使用）。"""

    amap_web_service_key: str = ""
    """高德 Web 服务 Key。为空时行政区搜索接口不可用，不影响其他功能。"""

    # 允许跨域的前端来源，逗号分隔
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def _make_sqlite_path_absolute(cls, value: str) -> str:
        """把相对的 SQLite 路径固定到 backend/ 下。"""

        value = value.strip()

        if not value:
            return DEFAULT_DATABASE_URL

        if not value.startswith(_SQLITE_PREFIX):
            return value

        raw_path = value[len(_SQLITE_PREFIX) :]

        if raw_path == ":memory:" or raw_path == "":
            return value

        path = Path(raw_path)

        if path.is_absolute():
            return value

        return f"{_SQLITE_PREFIX}{(BACKEND_DIR / path).resolve().as_posix()}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
