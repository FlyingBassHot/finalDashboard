"""集成注册表 —— 集成类型的注册与实例化。"""

from collections.abc import Callable

from app.domain.capability import CONTROL_CAPABILITIES
from app.plugins.contract import (
    Integration,
    IntegrationContext,
    PollingIntegration,
)
from app.plugins.errors import (
    IntegrationConfigError,
    UnknownIntegrationError,
)
from app.plugins.manifest import IntegrationManifest

IntegrationFactory = Callable[[IntegrationContext], Integration]


class IntegrationRegistry:
    """管理「集成名 → 清单 + 工厂」的注册表。

    注册幂等性:同名重复注册视为开发期错误,直接抛出。
    实例的创建 / 启停 / 轮询调度由上层运行器(后续 tasks 层)
    驱动,注册表只负责类型层面的事。
    """

    def __init__(self) -> None:
        self._factories: dict[str, type[Integration]] = {}
        self._manifests: dict[str, IntegrationManifest] = {}

    def register(self, integration_cls: type[Integration]) -> None:
        """注册一个集成类型(要求类上定义 manifest)。"""

        if not (
            isinstance(integration_cls, type)
            and issubclass(integration_cls, Integration)
        ):
            raise IntegrationConfigError(
                f"{integration_cls!r} 不是 Integration 的子类",
            )

        manifest = getattr(integration_cls, "manifest", None)

        if not isinstance(manifest, IntegrationManifest):
            raise IntegrationConfigError(
                f"{integration_cls.__name__} 缺少合法的 manifest ClassVar",
            )

        if issubclass(integration_cls, PollingIntegration):
            control_capabilities = manifest.capabilities & CONTROL_CAPABILITIES

            if control_capabilities:
                names = sorted(capability.value for capability in control_capabilities)

                raise IntegrationConfigError(
                    f"只读集成 {manifest.name} 不能声明写能力: {names}",
                )

        name = manifest.name

        if name in self._manifests:
            raise IntegrationConfigError(f"集成重复注册: {name}")

        self._manifests[name] = manifest
        self._factories[name] = integration_cls

    def create(
        self,
        name: str,
        context: IntegrationContext,
    ) -> Integration:
        """创建集成实例(注入上下文)。"""

        factory = self._factories.get(name)

        if factory is None:
            raise UnknownIntegrationError(f"未注册的集成: {name}")

        return factory(context)

    def manifest(self, name: str) -> IntegrationManifest:
        result = self._manifests.get(name)

        if result is None:
            raise UnknownIntegrationError(f"未注册的集成: {name}")

        return result

    def manifests(self) -> list[IntegrationManifest]:
        """全部已注册集成清单(按注册顺序)。"""

        return list(self._manifests.values())

    def names(self) -> list[str]:
        """全部已注册集成名(按注册顺序)。"""

        return list(self._manifests)

    def __contains__(self, name: str) -> bool:
        return name in self._manifests


default_registry = IntegrationRegistry()
"""进程级默认注册表。"""


def register_integration(
    integration_cls: type[Integration],
) -> type[Integration]:
    """类装饰器:注册到默认注册表。"""

    default_registry.register(integration_cls)

    return integration_cls
