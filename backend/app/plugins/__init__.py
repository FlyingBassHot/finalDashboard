"""plugins — 插件运行时(框架)。

集成契约与「唯一写通道」ActionGateway 都在这里;
具体集成实现见 app/integrations/。
"""

from app.plugins.action_gateway import (
    ActionAuditRecord,
    ActionGateway,
    ActionRequest,
    ActionResult,
    AuditSink,
)
from app.plugins.catalog import EntityCatalog
from app.plugins.context import BaseIntegrationContext
from app.plugins.contract import (
    HybridIntegration,
    Integration,
    IntegrationContext,
    PollingIntegration,
    SubscribingIntegration,
)
from app.plugins.errors import (
    ActionExecutionError,
    IntegrationConfigError,
    IntegrationError,
    UnknownIntegrationError,
    UnsupportedActionError,
)
from app.plugins.manifest import CollectionMode, IntegrationManifest
from app.plugins.registry import (
    IntegrationRegistry,
    default_registry,
    register_integration,
)

__all__ = [
    "ActionAuditRecord",
    "ActionExecutionError",
    "ActionGateway",
    "ActionRequest",
    "ActionResult",
    "AuditSink",
    "BaseIntegrationContext",
    "EntityCatalog",
    "CollectionMode",
    "HybridIntegration",
    "Integration",
    "IntegrationConfigError",
    "IntegrationContext",
    "IntegrationError",
    "IntegrationManifest",
    "IntegrationRegistry",
    "PollingIntegration",
    "SubscribingIntegration",
    "UnknownIntegrationError",
    "UnsupportedActionError",
    "default_registry",
    "register_integration",
]
