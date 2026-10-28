"""动作网关 —— 全底座唯一的写通道。

职责(按顺序):

1. 集成级白名单:动作能力必须包含在集成 manifest 中;
2. 实体存在性:目标实体必须已注册在目录中;
3. 归属校验:目标实体必须属于发起动作的集成;
4. 实体级白名单:目标实体必须声明该能力;
5. 转发给集成执行,统一异常归一;
6. 全程审计(允许 / 拒绝 / 失败都留痕)。

边界哲学:第一类设备只读集成 manifest 只声明 READONLY,
任何动作请求在第一关就被类型级拒绝 —— 不依赖实现者自觉。
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.capability import Capability
from app.plugins.catalog import EntityCatalog
from app.plugins.contract import (
    ActionRequest,
    ActionResult,
    Integration,
)
from app.plugins.errors import (
    ActionExecutionError,
    IntegrationError,
    UnsupportedActionError,
)
from app.plugins.manifest import IntegrationManifest


@dataclass(frozen=True, slots=True)
class ActionAuditRecord:
    """动作审计记录(允许 / 拒绝 / 失败均产生)。"""

    integration: str
    entity_id: str
    action: str
    capability: Capability
    outcome: str
    """ok / rejected:<原因> / error:<原因>"""

    message: str = ""

    occurred_at: datetime | None = None
    """记录时刻(默认为记录创建时刻)。"""

    def __post_init__(self) -> None:
        if self.occurred_at is None:
            object.__setattr__(
                self,
                "occurred_at",
                datetime.now(UTC),
            )


AuditSink = Callable[[ActionAuditRecord], None]


def _default_audit_sink(record: ActionAuditRecord) -> None:
    logging.getLogger("app.plugins.audit").info(
        "action audit: %s %s %s -> %s %s",
        record.integration,
        record.entity_id,
        record.action,
        record.outcome,
        record.message,
    )


class ActionGateway:
    """动作执行网关。

    实例由调用方(API 层)持有,网关不管理集成生命周期,
    只做校验 / 转发 / 审计,职责单一。
    """

    def __init__(
        self,
        catalog: EntityCatalog,
        audit: AuditSink | None = None,
    ) -> None:
        self._catalog = catalog
        self._audit: AuditSink = audit or _default_audit_sink

    async def execute(
        self,
        integration: Integration,
        request: ActionRequest,
    ) -> ActionResult:
        """校验并执行一个动作请求。

        抛出:
        - UnsupportedActionError:能力白名单拒绝(→ 4xx)
        - ActionExecutionError:执行失败 / 实体不存在
        """

        manifest: IntegrationManifest = integration.manifest

        # 第一关:集成级能力白名单
        if request.capability not in manifest.capabilities:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome="rejected:manifest",
                    message="集成未声明该能力",
                ),
            )

            raise UnsupportedActionError(
                f"集成 {manifest.name} 未声明能力 {request.capability.value},拒绝执行",
            )

        # 第二关:实体必须存在且声明该能力
        entity = self._catalog.find_entity(
            request.entity_id,
        )

        if entity is None:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome="rejected:entity-missing",
                    message="目标实体不存在",
                ),
            )

            raise ActionExecutionError(
                f"实体不存在: {request.entity_id}",
            )

        if entity.integration != manifest.name:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome="rejected:entity-owner",
                    message=f"实体属于集成 {entity.integration!r}",
                ),
            )

            raise UnsupportedActionError(
                f"实体 {request.entity_id} 属于集成 "
                f"{entity.integration!r},不允许由 {manifest.name} 操作",
            )

        if request.capability not in entity.capabilities:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome="rejected:entity-capability",
                    message="实体未声明该能力",
                ),
            )

            raise UnsupportedActionError(
                f"实体 {request.entity_id} 未声明能力 {request.capability.value}",
            )

        # 转发执行(异常归一 + 审计)
        try:
            result = await integration.execute_action(
                request,
            )

        except IntegrationError as exc:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome=f"error:{type(exc).__name__}",
                    message=str(exc),
                ),
            )

            raise

        except Exception as exc:
            self._audit(
                ActionAuditRecord(
                    integration=manifest.name,
                    entity_id=request.entity_id,
                    action=request.action,
                    capability=request.capability,
                    outcome="error:unexpected",
                    message=str(exc),
                ),
            )

            raise ActionExecutionError(
                f"动作执行失败: {request.action}",
            ) from exc

        self._audit(
            ActionAuditRecord(
                integration=manifest.name,
                entity_id=request.entity_id,
                action=request.action,
                capability=request.capability,
                outcome="ok",
                message=result.message,
            ),
        )

        return result
