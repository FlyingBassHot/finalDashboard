"""从数据库生成 Prometheus 文本暴露格式（0.0.4）。"""

import math
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.repositories.devices import DeviceRepository
from app.repositories.entities import EntityRepository
from app.repositories.entity_states import EntityStateRepository
from app.repositories.integration_instances import (
    IntegrationInstanceRepository,
)

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(labels: dict[str, str | None]) -> str:
    if not labels:
        return ""

    body = ",".join(
        f'{key}="{_escape("" if value is None else str(value))}"'
        for key, value in sorted(labels.items())
    )

    return f"{{{body}}}"


def _format_value(value: Any) -> str | None:
    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"

        if math.isinf(value):
            return "+Inf" if value > 0 else "-Inf"

        return repr(value)

    return None


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None

    return f"{value.timestamp():.3f}"


def _metric(
    lines: list[str],
    name: str,
    help_text: str,
    metric_type: str,
    samples: Iterable[tuple[dict[str, str | None], Any]],
) -> None:
    lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} {metric_type}")

    for labels, value in samples:
        formatted = _format_value(value)

        if formatted is None:
            continue

        lines.append(f"{name}{_labels(labels)} {formatted}")


def _timestamp_metric(
    lines: list[str],
    name: str,
    help_text: str,
    samples: Iterable[tuple[dict[str, str | None], datetime | None]],
) -> None:
    lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} gauge")

    for labels, value in samples:
        formatted = _format_timestamp(value)

        if formatted is None:
            continue

        lines.append(f"{name}{_labels(labels)} {formatted}")


async def render_metrics(db: AsyncSession) -> str:
    devices = await DeviceRepository().list(db)
    entities = await EntityRepository().list(db)
    states = {row.entity_id: row for row in await EntityStateRepository().list(db)}
    instances = await IntegrationInstanceRepository().list(db)

    lines: list[str] = []

    lines.append("# HELP homehub_build_info Home Hub build info")
    lines.append("# TYPE homehub_build_info gauge")
    lines.append(
        f"homehub_build_info{_labels({'version': __version__})} 1",
    )

    _metric(
        lines,
        "homehub_device_up",
        "Device availability (1=up, 0=down)",
        "gauge",
        [
            (
                {
                    "device_id": device.device_id,
                    "integration": device.integration,
                    "instance_name": device.instance_name,
                    "category": device.category,
                },
                device.available,
            )
            for device in devices
        ],
    )

    _metric(
        lines,
        "homehub_device_info",
        "Static device metadata",
        "gauge",
        [
            (
                {
                    "device_id": device.device_id,
                    "integration": device.integration,
                    "instance_name": device.instance_name,
                    "name": device.name,
                    "category": device.category,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                },
                1,
            )
            for device in devices
        ],
    )

    _metric(
        lines,
        "homehub_entity_info",
        "Entity metadata",
        "gauge",
        [
            (
                {
                    "entity_id": entity.entity_id,
                    "integration": entity.integration,
                    "device_id": entity.device_id,
                    "domain": entity.domain,
                    "name": entity.name,
                    "unit": entity.unit,
                },
                1,
            )
            for entity in entities
        ],
    )

    _metric(
        lines,
        "homehub_entity_state",
        "Current numeric entity state",
        "gauge",
        [
            (
                {
                    "entity_id": entity.entity_id,
                    "integration": entity.integration,
                    "device_id": entity.device_id,
                    "domain": entity.domain,
                    "unit": entity.unit,
                },
                states[entity.entity_id].value,
            )
            for entity in entities
            if entity.entity_id in states
            and _format_value(states[entity.entity_id].value) is not None
        ],
    )

    _metric(
        lines,
        "homehub_integration_enabled",
        "Integration instance enabled flag",
        "gauge",
        [
            (
                {
                    "instance_name": instance.name,
                    "integration": instance.integration,
                },
                instance.enabled,
            )
            for instance in instances
        ],
    )

    _metric(
        lines,
        "homehub_integration_healthy",
        "Integration instance healthy (enabled, no error, polled successfully)",
        "gauge",
        [
            (
                {
                    "instance_name": instance.name,
                    "integration": instance.integration,
                },
                (
                    instance.enabled
                    and instance.last_error is None
                    and instance.last_success_at is not None
                ),
            )
            for instance in instances
        ],
    )

    _timestamp_metric(
        lines,
        "homehub_integration_last_poll_timestamp_seconds",
        "Last poll attempt timestamp",
        [
            (
                {
                    "instance_name": instance.name,
                    "integration": instance.integration,
                },
                instance.last_poll_at,
            )
            for instance in instances
        ],
    )

    _timestamp_metric(
        lines,
        "homehub_integration_last_success_timestamp_seconds",
        "Last successful poll timestamp",
        [
            (
                {
                    "instance_name": instance.name,
                    "integration": instance.integration,
                },
                instance.last_success_at,
            )
            for instance in instances
        ],
    )

    return "\n".join(lines) + "\n"
