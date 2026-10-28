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

    integration: str = ""
    """注册后由框架填充的集成名(组成 device_id 用)。"""

    @property
    def device_id(self) -> str:
        """全局唯一 ID:<integration>.<key>"""

        if self.integration:
            return f"{self.integration}.{self.key}"

        return self.key
