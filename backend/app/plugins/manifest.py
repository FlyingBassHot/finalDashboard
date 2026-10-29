"""集成清单 —— 每个集成注册时必须提供的自描述元数据。"""

import re
from dataclasses import dataclass
from enum import StrEnum

from app.domain.capability import Capability
from app.domain.device import DeviceCategory
from app.plugins.errors import IntegrationConfigError

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class CollectionMode(StrEnum):
    """集成与设备交互的触发方式。"""

    POLL = "poll"
    """框架按间隔主动拉取。"""

    SUBSCRIBE = "subscribe"
    """集成持有长连接 / 订阅，消息到达时主动上报。"""

    HYBRID = "hybrid"
    """同时需要定时刷新与长驻订阅。"""


@dataclass(frozen=True, slots=True)
class IntegrationManifest:
    """集成自描述。

    name 同时充当该集成全部实体 / 设备全局 ID 的前缀,
    因此强制小写 snake_case。
    """

    name: str
    """唯一标识,如 "openwrt"、"mqtt"。"""

    display_name: str
    """展示名,如 "OpenWrt 路由器"。"""

    description: str = ""

    collection_mode: CollectionMode = CollectionMode.POLL
    """采集触发方式：poll / subscribe / hybrid。"""

    capabilities: frozenset[Capability] = frozenset({Capability.READONLY})
    """集成整体能力边界。只读集成只声明 READONLY。"""

    supported_categories: frozenset[DeviceCategory] = frozenset(
        {DeviceCategory.UNKNOWN}
    )
    """可接入的设备类别。"""

    default_poll_interval_seconds: int = 60
    """默认轮询间隔(实例配置可覆盖；订阅型可忽略)。"""

    version: str = "0.1.0"

    requires_credentials: bool = True
    """是否需要凭据(供前端配置表单与文档使用)。"""

    def __post_init__(self) -> None:
        if not NAME_PATTERN.fullmatch(self.name):
            raise IntegrationConfigError(
                f"集成名非法(需小写 snake_case): {self.name!r}",
            )

        if not isinstance(self.collection_mode, CollectionMode):
            try:
                object.__setattr__(
                    self,
                    "collection_mode",
                    CollectionMode(self.collection_mode),
                )

            except ValueError as exc:
                raise IntegrationConfigError(
                    f"非法 collection_mode: {self.collection_mode!r}",
                ) from exc

        if not self.capabilities:
            raise IntegrationConfigError(
                f"集成 {self.name} 至少需要声明一个能力",
            )

        if self.default_poll_interval_seconds <= 0:
            raise IntegrationConfigError(
                f"集成 {self.name} 轮询间隔必须为正数",
            )

    def supports(
        self,
        capability: Capability,
    ) -> bool:
        """是否声明了某能力。"""

        return capability in self.capabilities
