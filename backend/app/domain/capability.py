"""能力模型 —— 底座功能边界的类型化表达。

能力在两个层面声明:

- 集成层(IntegrationManifest.capabilities):该集成整体允许做什么;
- 实体层(EntityDescriptor.capabilities):单个实体可被施加哪些操作。

「读总是安全的,写必须最小化」由 ActionGateway 强制:
未声明对应能力的集成 / 实体,动作请求会在类型层面被直接拒绝,
不依赖集成实现者的自觉。
"""

from enum import StrEnum


class Capability(StrEnum):
    """能力类别(语义对齐 Home Assistant 的 domain 体系)。"""

    READONLY = "readonly"
    """只读:传感器、指标、状态展示。第一类设备默认且唯一的能力。"""

    ON_OFF = "on_off"
    """开关:灯光 / 插座 / 开关(第二类设备)。"""

    SET_LEVEL = "set_level"
    """调节:亮度、色温、数值等连续量(第二类设备)。"""

    ACTION = "action"
    """离散安全动作:如 Wake-on-LAN。第一类设备唯一的非只读能力。"""


CONTROL_CAPABILITIES: frozenset[Capability] = frozenset(
    {
        Capability.ON_OFF,
        Capability.SET_LEVEL,
        Capability.ACTION,
    }
)
"""全部「写」能力 —— 必须经 ActionGateway 白名单校验。"""


def is_control(capability: Capability) -> bool:
    """判断能力是否为写能力(非只读)。"""

    return capability in CONTROL_CAPABILITIES
