"""领域事件 → 可传输的 JSON 结构。"""

from datetime import datetime
from typing import Any

from app.domain.device import DeviceDescriptor
from app.domain.entity import EntityDescriptor
from app.domain.events import (
    AlertReceivedEvent,
    DeviceAvailabilityEvent,
    DeviceRegisteredEvent,
    DomainEvent,
    EntityRegisteredEvent,
    NeighborReportEvent,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.domain.topology import Neighbor


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _state(value: EntityState | None) -> dict[str, Any] | None:
    if value is None:
        return None

    return {
        "value": value.value,
        "attributes": dict(value.attributes),
        "observed_at": _iso(value.observed_at),
    }


def _device(value: DeviceDescriptor | None) -> dict[str, Any] | None:
    if value is None:
        return None

    return {
        "device_id": value.device_id,
        "integration": value.integration,
        "instance": value.instance,
        "key": value.key,
        "name": value.name,
        "category": value.category.value,
        "manufacturer": value.manufacturer,
        "model": value.model,
        "sw_version": value.sw_version,
        "identity": value.identity,
    }


def _entity(value: EntityDescriptor | None) -> dict[str, Any] | None:
    if value is None:
        return None

    return {
        "entity_id": value.entity_id,
        "device_id": value.device_id,
        "integration": value.integration,
        "instance": value.instance,
        "key": value.key,
        "name": value.name,
        "domain": value.domain,
        "unit": value.unit,
        "icon": value.icon,
        "capabilities": sorted(capability.value for capability in value.capabilities),
        "attributes": dict(value.attributes),
    }


def _neighbor(value: Neighbor) -> dict[str, Any]:
    return {
        "mac": value.mac,
        "ip": value.ip,
        "hostname": value.hostname,
        "interface": value.interface,
        "source": value.source,
        "is_wireless": value.is_wireless,
    }


def serialize_event(event: DomainEvent) -> dict[str, Any] | None:
    """把领域事件转换成 ``{type, occurred_at, source, data}``。"""

    common = {
        "occurred_at": _iso(event.occurred_at),
        "source": event.source,
    }

    if isinstance(event, StateChangedEvent):
        return {
            "type": "state_changed",
            **common,
            "data": {
                "entity_id": event.entity_id,
                "old": _state(event.old),
                "new": _state(event.new),
            },
        }

    if isinstance(event, DeviceAvailabilityEvent):
        return {
            "type": "device_availability",
            **common,
            "data": {
                "device_id": event.device_id,
                "available": event.available,
            },
        }

    if isinstance(event, NeighborReportEvent):
        return {
            "type": "neighbor_report",
            **common,
            "data": {
                "device_id": event.device_id,
                "neighbors": [_neighbor(item) for item in event.neighbors],
            },
        }

    if isinstance(event, DeviceRegisteredEvent):
        return {
            "type": "device_registered",
            **common,
            "data": {"device": _device(event.device)},
        }

    if isinstance(event, AlertReceivedEvent):
        return {
            "type": "alert_received",
            **common,
            "data": {
                "fingerprint": event.fingerprint,
                "name": event.name,
                "status": event.status,
                "severity": event.severity,
                "summary": event.summary,
                "labels": dict(event.labels),
            },
        }

    if isinstance(event, EntityRegisteredEvent):
        return {
            "type": "entity_registered",
            **common,
            "data": {"entity": _entity(event.entity)},
        }

    return None
