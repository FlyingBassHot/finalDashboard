"""动作执行与审计的出入参。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.capability import Capability


class ActionExecuteRequest(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    capability: Capability
    params: dict[str, Any] = Field(default_factory=dict)


class ActionExecuteResponse(BaseModel):
    ok: bool
    message: str


class ActionAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration: str
    entity_id: str
    action: str
    capability: str
    outcome: str
    message: str
    occurred_at: datetime
    created_at: datetime
