"""设备 / 实体 / 状态的出参。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EntitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    device_id: str
    integration: str
    instance_name: str
    entity_key: str
    name: str
    domain: str
    unit: str | None
    icon: str | None
    capabilities: list[str]
    attributes: dict[str, Any] = Field(default_factory=dict)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    integration: str
    instance_name: str
    device_key: str
    identity: str | None
    name: str
    category: str
    manufacturer: str | None
    model: str | None
    sw_version: str | None
    available: bool
    last_seen_at: datetime | None
    updated_at: datetime

    entities: list[EntitySummary] = Field(default_factory=list)


class EntityResponse(EntitySummary):
    created_at: datetime
    updated_at: datetime


class EntityStateResponse(BaseModel):
    entity_id: str
    value: Any
    attributes: dict[str, Any]
    observed_at: datetime
    updated_at: datetime


class EntityHistoryResponse(BaseModel):
    entity_id: str
    value: Any
    attributes: dict[str, Any]
    observed_at: datetime
    recorded_at: datetime
