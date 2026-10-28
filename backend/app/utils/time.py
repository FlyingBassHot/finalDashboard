"""时间与时区工具。"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Shanghai"


def ensure_utc(value: datetime) -> datetime:
    """无时区按 UTC 解释，其余统一转 UTC。"""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def resolve_timezone(name: str | None) -> ZoneInfo:
    """解析 IANA 时区名，非法或缺失时退回家庭默认时区。"""

    if not name:
        return ZoneInfo(DEFAULT_TIMEZONE)

    try:
        return ZoneInfo(name)

    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TIMEZONE)


def to_local(value: datetime, name: str | None) -> datetime:
    """把时间转换到指定时区；无时区的时间按 UTC 解释。"""

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)

    return value.astimezone(resolve_timezone(name))


def to_timezone(
    value: datetime | None,
    name: str | None,
) -> datetime | None:
    """同 :func:`to_local`，但允许 None。"""

    if value is None:
        return None

    return to_local(value, name)
