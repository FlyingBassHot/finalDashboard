"""数据库时间类型：统一以 UTC 存取，读出时带回时区。

SQLite 本身不保存时区信息。如果不做统一约定，同一行里很容易混入
本地时间与 UTC（例如 Open-Meteo 的本地墙钟时间 vs 服务端 UTC），
相差数小时却无法从数据本身分辨。这里在绑定参数与结果两侧各做一次
归一化：

- 写入：无时区按 UTC 解释 → 转 UTC → 去掉 tzinfo 存库；
- 读出：补回 UTC tzinfo，调用方拿到的永远是 aware datetime。
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    """当前 UTC 时间（aware）。"""

    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """始终以 UTC 存取的 DateTime。"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)

        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)
