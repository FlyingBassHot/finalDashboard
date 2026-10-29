"""集成实例与清单的出入参。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.plugins.manifest import IntegrationManifest

SECRET_HINTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "***"
                if any(hint in str(key).lower() for hint in SECRET_HINTS)
                else _redact(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_redact(item) for item in value]

    return value


class IntegrationManifestResponse(BaseModel):
    name: str
    display_name: str
    description: str
    collection_mode: str
    capabilities: list[str]
    supported_categories: list[str]
    default_poll_interval_seconds: int
    version: str
    requires_credentials: bool

    @classmethod
    def from_manifest(
        cls,
        manifest: IntegrationManifest,
    ) -> "IntegrationManifestResponse":
        return cls(
            name=manifest.name,
            display_name=manifest.display_name,
            description=manifest.description,
            collection_mode=manifest.collection_mode.value,
            capabilities=sorted(
                capability.value for capability in manifest.capabilities
            ),
            supported_categories=sorted(
                category.value for category in manifest.supported_categories
            ),
            default_poll_interval_seconds=(manifest.default_poll_interval_seconds),
            version=manifest.version,
            requires_credentials=manifest.requires_credentials,
        )


class IntegrationInstanceCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    integration: str = Field(min_length=1, max_length=64)

    display_name: str | None = Field(default=None, max_length=200)

    config: dict[str, Any] = Field(default_factory=dict)

    poll_interval_seconds: int | None = Field(
        default=None,
        ge=1,
        le=86_400,
    )

    enabled: bool = True


class IntegrationInstanceUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    config: dict[str, Any] | None = None
    poll_interval_seconds: int | None = Field(
        default=None,
        ge=1,
        le=86_400,
    )
    enabled: bool | None = None


class IntegrationInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    integration: str
    display_name: str
    config: dict[str, Any]
    poll_interval_seconds: int
    enabled: bool

    last_started_at: datetime | None
    last_poll_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None

    created_at: datetime
    updated_at: datetime

    @field_serializer("config")
    def _serialize_config(self, value: dict[str, Any]) -> dict[str, Any]:
        """响应中脱敏敏感配置；写接口仍接受完整配置。"""

        return _redact(value)
