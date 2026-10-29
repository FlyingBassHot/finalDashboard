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

from app.domain.capability import (
    CONTROL_CAPABILITIES,
    Capability,
)
from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.domain.topology import Neighbor
from app.plugins.errors import (
    IntegrationConfigError,
    UnsupportedActionError,
)
from app.plugins.manifest import CollectionMode, IntegrationManifest


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

    instance: str
    """集成实例名（框架注入，用于隔离同一集成的多个实例）。"""

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
    动作。这里做两层强制:

    1. 子类的 manifest 不得声明任何写能力(类创建时即报错);
    2. ``execute_action`` 被永久覆写为拒绝,子类即使再覆写,
       ActionGateway 也会因缺少清单能力而拒绝。
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        manifest = getattr(cls, "manifest", None)

        if isinstance(manifest, IntegrationManifest):
            if manifest.collection_mode is not CollectionMode.POLL:
                raise IntegrationConfigError(
                    f"PollingIntegration {manifest.name} 的 collection_mode "
                    f"必须是 poll，收到 {manifest.collection_mode.value}",
                )

            control_capabilities = manifest.capabilities & CONTROL_CAPABILITIES

            if control_capabilities:
                names = ", ".join(
                    sorted(capability.value for capability in control_capabilities),
                )

                raise IntegrationConfigError(
                    f"只读集成 {manifest.name} 不能声明写能力: {names}",
                )

    async def execute_action(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        raise UnsupportedActionError(
            f"只读集成 {type(self).__name__} 不允许执行任何动作",
        )

    @abstractmethod
    async def poll(self) -> None:
        """周期采集:register / emit 设备与实体状态。"""


class SubscribingIntegration(Integration):
    """推送型集成基类（MQTT / WebSocket 等）。

    ``start()`` 是一个长驻协程：连接、订阅、收到消息时调用
    ``context.emit_state`` 等；连接断开可以抛异常，由运行器按退避重连。
    运行器停止实例时会取消该任务，并调用 ``stop()`` 做清理。

    与 PollingIntegration 不同，本类不限制写能力——第二类设备可能需要
    on_off / set_level，是否允许仍由 manifest 与 ActionGateway 决定。
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        manifest = getattr(cls, "manifest", None)

        if (
            isinstance(manifest, IntegrationManifest)
            and manifest.collection_mode is not CollectionMode.SUBSCRIBE
        ):
            raise IntegrationConfigError(
                f"SubscribingIntegration {manifest.name} 的 collection_mode "
                f"必须是 subscribe，收到 {manifest.collection_mode.value}",
            )

    @abstractmethod
    async def start(self) -> None:
        """长驻订阅循环；返回或抛异常表示本次连接结束。"""

    async def stop(self) -> None:
        """请求停止订阅（可选，默认无操作）。"""


class HybridIntegration(Integration):
    """混合型集成：既需要定时刷新，也需要长驻订阅（如 ONVIF）。

    运行器会同时调度 ``poll()`` 并监管 ``start()`` 任务。
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        manifest = getattr(cls, "manifest", None)

        if (
            isinstance(manifest, IntegrationManifest)
            and manifest.collection_mode is not CollectionMode.HYBRID
        ):
            raise IntegrationConfigError(
                f"HybridIntegration {manifest.name} 的 collection_mode "
                f"必须是 hybrid，收到 {manifest.collection_mode.value}",
            )

    @abstractmethod
    async def poll(self) -> None:
        """定时刷新：设备信息、健康状态等。"""

    @abstractmethod
    async def start(self) -> None:
        """长驻订阅循环；返回或抛异常表示本次连接结束。"""

    async def stop(self) -> None:
        """请求停止订阅（可选，默认无操作）。"""
