"""集成注册表 —— 集成类型的注册与实例化。"""

from collections.abc import Callable

from app.plugins.contract import (
    Integration,
    IntegrationContext,
)
from app.plugins.errors import (
    IntegrationConfigError,
    UnknownIntegrationError,
)
from app.plugins.manifest import IntegrationManifest

IntegrationFactory = Callable[
    [IntegrationContext],
    Integration,
]


class IntegrationRegistry:
    """管理「集成名 → 清单 + 工厂」的注册表。

    注册幂等性:同名重复注册视为开发期错误,直接抛出。
    实例的创建 / 启停 / 轮询调度由上层运行器(后续 tasks 层)
    驱动,注册表只负责类型层面的事。
    """

    def __init__(self) -> None:
        self._factories: dict[str, IntegrationFactory] = {}
        self._manifests: dict[str, IntegrationManifest] = {}

    def register(
        self,
        integration_cls: type[Integration],
    ) -> None:
        """注册一个集成类型(要求类上定义 manifest)。"""

        manifest = getattr(
            integration_cls,
            "manifest",
            None,
        )

        if not isinstance(manifest, IntegrationManifest):
            raise IntegrationConfigError(
                f"{integration_cls.__name__} 缺少合法的 "
                f"manifest ClassVar",
            )

        name = manifest.name

        if name in self._manifests:
            raise IntegrationConfigError(
                f"集成重复注册: {name}",
            )

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
            raise UnknownIntegrationError(
                f"未注册的集成: {name}",
            )

        return factory(context)

    def manifest(
        self,
        name: str,
    ) -> IntegrationManifest:
        result = self._manifests.get(name)

        if result is None:
            raise UnknownIntegrationError(
                f"未注册的集成: {name}",
            )

        return result

    def manifests(self) -> list[IntegrationManifest]:
        """全部已注册集成清单(按注册顺序)。"""

        return list(self._manifests.values())

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
