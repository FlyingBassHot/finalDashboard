"""实体状态 —— 不可变值对象。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EntityState:
    """某实体在某个时刻的状态快照。

    - value:主值(sensor 数值、binary_sensor 布尔、文本状态等)
    - attributes:附加属性(如负载详情、信号强度、SSID)
    - observed_at:观测时刻(UTC);缺省时由框架补为收到时刻
    """

    value: Any = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        # 复制一份可变映射,避免外部共享可变状态
        object.__setattr__(
            self,
            "attributes",
            dict(self.attributes),
        )

        if self.observed_at is None:
            object.__setattr__(
                self,
                "observed_at",
                datetime.now(timezone.utc),
            )
