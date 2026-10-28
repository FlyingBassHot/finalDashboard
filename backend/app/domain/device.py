"""设备描述符与设备类别。"""

from dataclasses import dataclass
from enum import StrEnum


class DeviceCategory(StrEnum):
    """设备类别。

    当前落地第一类(开源 OS 设备);第二类(厂商智能设备)
    的类别在后续阶段扩展。
    """

    ROUTER = "router"
    """路由器 / OpenWrt 设备。"""

    NAS = "nas"
    """NAS 存储。"""

    CAMERA = "camera"
    """网络摄像头。"""

    COMPUTER = "computer"
    """Linux / Windows PC。"""

    GATEWAY = "gateway"
    """智能家居网关(第二类预留)。"""

    SENSOR = "sensor"
    """智能传感器 / 执行器(第二类预留)。"""

    UNKNOWN = "unknown"
    """未分类。"""


@dataclass(frozen=True, slots=True)
class DeviceDescriptor:
    """设备声明(静态元信息)。"""

    key: str
    """集成内唯一设备标识。"""

    name: str
    """展示名,如 "客厅路由器"。"""

    category: DeviceCategory = DeviceCategory.UNKNOWN
    manufacturer: str | None = None
    model: str | None = None
    sw_version: str | None = None

    identity: str | None = None
    """稳定硬件标识,如 "mac:aa:bb:cc:dd:ee:ff" / "serial:ABC123"。

    用于拓扑匹配与未来多协议归并;同一条目在不同集成间保持一致,
    但当前不据此合并 device_id(见 docs/DECISIONS.md ADR-001)。
    """

    integration: str = ""
    """注册后由框架填充的集成名(组成 device_id 用)。"""

    instance: str = ""
    """集成实例名(由框架在注册时填充),用于隔离同一集成的多个实例。"""

    @property
    def device_id(self) -> str:
        """全局唯一 ID:<integration>.<instance>.<key>"""

        return ".".join(
            part for part in [self.integration, self.instance, self.key] if part
        )
