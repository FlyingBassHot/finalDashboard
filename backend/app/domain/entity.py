"""实体描述符 —— 集成注册实体时的静态声明。"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.domain.capability import Capability


@dataclass(frozen=True, slots=True)
class EntityDescriptor:
    """实体声明(仅静态元信息,运行时状态见 EntityState)。

    全局唯一 ID 由四段组成:`<integration>.<instance>.<device_key>.<key>`,
    其中 integration / instance 由框架在注册时填充(见 IntegrationContext)。
    单实例场景下 instance 为空时退化为三段式。
    """

    key: str
    """集成内唯一,如 "cpu_load"、"wlan0_clients"。"""

    name: str
    """展示名,如 "CPU 负载"。"""

    domain: str
    """HA 语义域:"sensor" / "binary_sensor" / "switch" / "light" / "number"…"""

    device_key: str = ""
    """所属设备的 key(集成内)。空 = 挂在集成自身虚拟设备下。"""

    capabilities: frozenset[Capability] = frozenset({Capability.READONLY})
    """该实体可被施加的操作类别,默认只读。"""

    unit: str | None = None
    """计量单位("%"、"°C"、"MB" 等)。"""

    icon: str | None = None
    """前端图标 key(可选)。"""

    attributes: Mapping[str, Any] = field(default_factory=dict)
    """适配器扩展元数据。

    用于放置协议特有、但不属于核心语义的信息(如采样周期、原始字段名、
    展示精度)。北向原样透出,核心逻辑不依赖其内容。
    """

    integration: str = ""
    """注册后由框架填充的集成名(组成 entity_id 用)。"""

    instance: str = ""
    """集成实例名(由框架在注册时填充)。"""

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))

    @property
    def device_id(self) -> str:
        """所属设备 ID:<integration>.<instance>.<device_key>"""

        return ".".join(
            part for part in [self.integration, self.instance, self.device_key] if part
        )

    @property
    def entity_id(self) -> str:
        """全局唯一 ID:<integration>.<instance>.<device_key>.<key>"""

        parts = [
            self.integration,
            self.instance,
            self.device_key,
            self.key,
        ]

        return ".".join(part for part in parts if part)
