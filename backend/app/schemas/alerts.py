"""Alertmanager webhook 与告警查询的出入参。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AlertmanagerAlert(BaseModel):
    status: Literal["firing", "resolved"]

    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)

    startsAt: datetime | None = None
    endsAt: datetime | None = None
    generatorURL: str | None = None
    fingerprint: str | None = None


class AlertmanagerPayload(BaseModel):
    version: str = "4"
    status: str = ""
    receiver: str = ""
    groupKey: str = ""

    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)

    externalURL: str = ""
    truncatedAlerts: int = 0

    alerts: list[AlertmanagerAlert] = Field(default_factory=list)


class AlertWebhookResponse(BaseModel):
    status: str = "ok"
    received: int


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fingerprint: str
    name: str
    status: str
    severity: str

    summary: str | None
    description: str | None

    labels: dict[str, Any]
    annotations: dict[str, Any]

    starts_at: datetime | None
    ends_at: datetime | None
    last_received_at: datetime
    resolved_at: datetime | None

    generator_url: str | None
    external_url: str | None
    receiver: str | None
    group_key: str | None

    received_count: int
