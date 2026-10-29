"""Prometheus exporter 抓取集成（第一类 · 只读）。

抓取 node_exporter 等标准 /metrics 端点，只读采集主机状态。
不在设备侧安装任何 agent；exporter 本来就暴露这些指标。
"""

import re
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlparse

from app.domain.capability import Capability
from app.domain.device import DeviceCategory, DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.state import EntityState
from app.integrations.prometheus_scrape.client import ExporterClient
from app.integrations.prometheus_scrape.mapping import (
    build_readings,
    parse_exposition,
)
from app.plugins.contract import PollingIntegration
from app.plugins.errors import IntegrationConfigError
from app.plugins.manifest import IntegrationManifest
from app.plugins.registry import register_integration

MAC_PATTERN = re.compile(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}")
DEVICE_KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]+")
SUPPORTED_CATEGORIES = {DeviceCategory.COMPUTER, DeviceCategory.NAS}


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}

    return default


@register_integration
class PrometheusScrapeIntegration(PollingIntegration):
    manifest = IntegrationManifest(
        name="prometheus_scrape",
        display_name="Prometheus exporter 抓取",
        description=(
            "抓取 node_exporter 等标准 /metrics 端点，只读采集 CPU 负载、"
            "内存、磁盘与运行时长。"
        ),
        capabilities=frozenset({Capability.READONLY}),
        supported_categories=frozenset(SUPPORTED_CATEGORIES),
        default_poll_interval_seconds=60,
        requires_credentials=False,
    )

    def __init__(self, context) -> None:
        super().__init__(context)

        self._client: ExporterClient | None = None
        self._device: DeviceDescriptor | None = None
        self._device_key = "main"
        self._disk_mountpoint = "/"

        self.client_factory: Callable[
            [Mapping[str, Any]],
            ExporterClient,
        ] = self._default_client_factory

    def _default_client_factory(
        self,
        config: Mapping[str, Any],
    ) -> ExporterClient:
        return ExporterClient(
            str(config.get("url", "")).strip(),
            verify_tls=_as_bool(config.get("verify_tls"), True),
            timeout=float(config.get("timeout", 10.0)),
            bearer_token=str(config.get("bearer_token", "")),
        )

    async def setup(self) -> None:
        config = self.context.config
        url = str(config.get("url", "")).strip()
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise IntegrationConfigError(
                "prometheus_scrape 需要配置完整的 url，例如 http://host:9100/metrics",
            )

        device_key = str(config.get("device_key", "main"))

        if not DEVICE_KEY_PATTERN.fullmatch(device_key):
            raise IntegrationConfigError(f"非法 device_key: {device_key!r}")

        self._device_key = device_key
        self._disk_mountpoint = str(config.get("disk_mountpoint", "/")) or "/"
        self._client = self.client_factory(config)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    async def discover(self) -> list[DeviceDescriptor]:
        config = self.context.config
        url = str(config.get("url", "")).strip()
        host = urlparse(url).hostname or "exporter"

        category_value = str(config.get("category", DeviceCategory.COMPUTER.value))

        try:
            category = DeviceCategory(category_value)

        except ValueError as exc:
            raise IntegrationConfigError(
                f"不支持的 category: {category_value!r}",
            ) from exc

        if category not in SUPPORTED_CATEGORIES:
            raise IntegrationConfigError(
                f"prometheus_scrape 只支持 computer / nas，收到: {category.value}",
            )

        identity = None
        mac = str(config.get("mac", "")).strip().lower()

        if mac:
            if not MAC_PATTERN.fullmatch(mac):
                raise IntegrationConfigError(f"非法 mac: {mac!r}")

            identity = f"mac:{mac}"

        device = DeviceDescriptor(
            key=self._device_key,
            name=str(config.get("name") or host),
            category=category,
            identity=identity,
        )

        self._device = device

        return [device]

    async def poll(self) -> None:
        assert self._client is not None
        assert self._device is not None

        try:
            text = await self._client.fetch()
            readings = build_readings(
                parse_exposition(text),
                disk_mountpoint=self._disk_mountpoint,
            )

            for reading in readings:
                entity = await self.context.register_entity(
                    EntityDescriptor(
                        key=reading.key,
                        name=reading.name,
                        domain=reading.domain,
                        device_key=self._device.key,
                        unit=reading.unit,
                    ),
                )
                await self.context.emit_state(
                    entity,
                    EntityState(value=reading.value),
                )

        except Exception:
            await self.context.emit_device_availability(self._device, False)
            raise

        await self.context.emit_device_availability(self._device, True)
