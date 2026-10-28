"""时间语义回归测试：UTC 入库、家庭时区输出。"""

from datetime import UTC, datetime

from app.collectors.weather.parser import parse_current_weather
from app.core.config import BACKEND_DIR, DEFAULT_DATABASE_URL, Settings
from app.core.db_types import UTCDateTime
from app.utils.time import resolve_timezone, to_local, to_timezone

SAMPLE_PAYLOAD = {
    "latitude": 34.05,
    "longitude": 113.82,
    "current": {
        "temperature_2m": 15.8,
        "relative_humidity_2m": 79,
        "apparent_temperature": 15.4,
        "wind_speed_10m": 7.6,
        "weather_code": 3,
        "is_day": 0,
        "time": "2026-10-28T10:15",
    },
    "daily": {
        "time": ["2026-10-28"],
        "weather_code": [51],
        "temperature_2m_max": [20.5],
        "temperature_2m_min": [12.8],
        "precipitation_probability_max": [100],
        "precipitation_sum": [0.8],
        "sunrise": ["2026-10-27T22:40"],
        "sunset": ["2026-10-28T09:36"],
    },
}


def test_parser_normalizes_all_times_to_utc() -> None:
    parsed = parse_current_weather(SAMPLE_PAYLOAD)

    observed_at = parsed["current"]["observed_at"]
    sunrise = parsed["daily"][0]["sunrise"]

    assert observed_at == datetime(2026, 10, 28, 10, 15, tzinfo=UTC)
    assert sunrise == datetime(2026, 10, 27, 22, 40, tzinfo=UTC)
    assert observed_at.tzinfo is not None
    assert sunrise.tzinfo is not None


def test_to_local_uses_home_timezone() -> None:
    utc_time = datetime(2026, 10, 28, 10, 15, tzinfo=UTC)

    local = to_local(utc_time, "Asia/Shanghai")

    assert local.hour == 18
    assert local.utcoffset() is not None
    assert local.utcoffset().total_seconds() == 8 * 3600


def test_naive_datetime_is_treated_as_utc() -> None:
    naive = datetime(2026, 10, 28, 10, 15)

    assert to_local(naive, "Asia/Shanghai").hour == 18


def test_unknown_timezone_falls_back() -> None:
    assert str(resolve_timezone("Not/AZone")) == "Asia/Shanghai"
    assert to_timezone(None, "Asia/Shanghai") is None


def test_utc_datetime_type_roundtrip() -> None:
    column = UTCDateTime()
    aware = datetime(2026, 10, 28, 10, 15, tzinfo=UTC)

    stored = column.process_bind_param(aware, None)
    loaded = column.process_result_value(stored, None)

    assert stored is not None and stored.tzinfo is None
    assert loaded == aware
    assert loaded is not None and loaded.tzinfo is not None


def test_relative_sqlite_path_is_resolved_under_backend() -> None:
    config = Settings(
        database_url="sqlite+aiosqlite:///./data/example.db",
        _env_file=None,
    )

    assert config.database_url.endswith("/backend/data/example.db")
    assert config.database_url.startswith("sqlite+aiosqlite:///")


def test_default_database_url_points_to_backend_data() -> None:
    config = Settings(_env_file=None)

    assert config.database_url == DEFAULT_DATABASE_URL
    assert config.database_url.endswith(f"/{BACKEND_DIR.name}/data/home_hub.db")


def test_empty_database_url_falls_back_to_default() -> None:
    config = Settings(database_url="", _env_file=None)

    assert config.database_url == DEFAULT_DATABASE_URL
