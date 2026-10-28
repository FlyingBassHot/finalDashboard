"""实体描述符 —— 集成注册实体时的静态声明。"""

from dataclasses import dataclass

from app.domain.capability import Capability


@dataclass(frozen=True, slots=True)
class EntityDescriptor:
    """实体声明(仅静态元信息,运行时状态见 EntityState)。

    全局唯一 ID 由三段组成:`<integration>.<device_key>.<key>`,
    其中 integration 段由框架在注册时填充(见 IntegrationContext)。
    """

    key: str
    """集成内唯一,如 "cpu_load"、"wlan0_clients"。"""

    name: str
    """展示名,如 "CPU 负载"。"""

    domain: str
    """HA 语义域:"sensor" / "binary_sensor" / "switch" / "light" / "number"…"""

    device_key: str = ""
    """所属设备的 key(集成内)。空 = 挂在集成自身虚拟设备下。"""

    capabilities: frozenset[Capability] = frozenset(
        {Capability.READONLY}
    )
    """该实体可被施加的操作类别,默认只读。"""

    unit: str | None = None
    """计量单位("%"、"°C"、"MB" 等)。"""

    icon: str | None = None
    """前端图标 key(可选)。"""

    integration: str = ""
    """注册后由框架填充的集成名(组成 entity_id 用)。"""

    @property
    def entity_id(self) -> str:
        """全局唯一 ID:<integration>.<device_key>.<key>"""

        parts = [
            self.integration,
            self.device_key,
            self.key,
        ]

        return ".".join(
            part for part in parts if part
        )
