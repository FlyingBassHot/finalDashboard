"""集成契约 —— 所有南向集成必须遵守的接口。

「基类即边界」:

- 第一类只读集成继承 `PollingIntegration`:必须实现 poll,
  execute_action 在基类被硬拒绝(无论子类怎么写);
- 需要安全动作(如 Wake-on-LAN)的集成继承 `Integration`
  并实现 execute_action —— 但动作仍会被 ActionGateway 校验:
  集成 manifest 与目标实体都必须声明对应能力,双重强制。
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from app.domain.capability import Capability
from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.plugins.errors import UnsupportedActionError
from app.plugins.manifest import IntegrationManifest


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """对某个实体发起的动作请求(全底座唯一写通道的载荷)。"""

    entity_id: str
    action: str
    """动作名(集成自定义,如 "wake")。"""

    capability: Capability
    """动作对应的能力类别 —— 网关据此做白名单校验。"""

    params: Mapping[str, Any] = field(
        default_factory=dict,
    )


@dataclass(frozen=True, slots=True)
class ActionResult:
    """动作执行结果。"""

    ok: bool
    message: str = ""


class IntegrationContext(Protocol):
    """框架注入给集成实例的运行环境。

    集成只能通过该上下文与底座交互:上报数据、读取自身配置。
    默认实现见 app.plugins.context.BaseIntegrationContext。
    """

    integration_name: str

    config: Mapping[str, Any]
    logger: logging.Logger

    async def register_device(
        self,
        device: DeviceDescriptor,
    ) -> DeviceDescriptor:
        """注册/更新设备声明,返回带 integration 前缀的规范化副本。"""
        ...

    async def register_entity(
        self,
        entity: EntityDescriptor,
    ) -> EntityDescriptor:
        """注册/更新实体声明,返回带 integration 前缀的规范化副本。"""
        ...

    async def emit_state(
        self,
        entity: EntityDescriptor,
        state: EntityState,
    ) -> None:
        """上报实体状态(触发 StateChangedEvent)。"""
        ...

    async def emit_device_availability(
        self,
        device: DeviceDescriptor,
        available: bool,
    ) -> None:
        """上报设备上下线(状态不变时自动去抖)。"""
        ...

    async def report_neighbors(
        self,
        device: DeviceDescriptor,
        neighbors: Sequence[Neighbor],
    ) -> None:
        """上报邻居表(供拓扑构建)。"""
        ...


class Integration(ABC):
    """集成基类 —— 所有南向适配器的共同契约。"""

    manifest: ClassVar[IntegrationManifest]
    """子类必须提供的清单(缺失时注册表会拒绝)。"""

    def __init__(
        self,
        context: IntegrationContext,
    ) -> None:
        self._context = context

    @property
    def context(self) -> IntegrationContext:
        return self._context

    async def setup(self) -> None:
        """可选:建立连接 / 预热。失败抛 IntegrationConnectionError。"""

    async def close(self) -> None:
        """可选:释放连接。框架停用实例时调用。"""

    @abstractmethod
    async def discover(self) -> list[DeviceDescriptor]:
        """声明该实例管理的设备(来自静态配置或协议发现)。"""

    async def poll(self) -> None:
        """周期采集。轮询型集成必须覆盖(见 PollingIntegration)。"""

    async def execute_action(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        """执行动作。默认拒绝一切 —— 能力边界由类型保证。"""

        raise UnsupportedActionError(
            f"集成 {type(self).__name__} 未实现任何动作",
        )


class PollingIntegration(Integration):
    """第一类只读集成的基类(周期轮询,零写能力)。

    继承本类即声明:该集成只会采集,不会也不允许下发任何
    动作 —— execute_action 在此被永久封死。
    """

    @abstractmethod
    async def poll(self) -> None:
        """周期采集:register / emit 设备与实体状态。"""
