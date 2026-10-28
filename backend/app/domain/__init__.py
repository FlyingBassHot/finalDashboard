"""domain — 统一领域模型(运行时)。

内部模型为 Home Assistant 风格 Entity;
WoT Thing Description 不进入本层(仅 export 层翻译)。
"""

from app.domain.capability import (
    CONTROL_CAPABILITIES,
    Capability,
    is_control,
)
from app.domain.device import (
    DeviceCategory,
    DeviceDescriptor,
)
from app.domain.entity import EntityDescriptor
from app.domain.events import (
    DeviceAvailabilityEvent,
    DeviceRegisteredEvent,
    DomainEvent,
    EntityRegisteredEvent,
    EventBus,
    NeighborReportEvent,
    StateChangedEvent,
)
from app.domain.state import EntityState
from app.domain.topology import Neighbor

__all__ = [
    "CONTROL_CAPABILITIES",
    "Capability",
    "DeviceAvailabilityEvent",
    "DeviceCategory",
    "DeviceDescriptor",
    "DeviceRegisteredEvent",
    "DomainEvent",
    "EntityDescriptor",
    "EntityRegisteredEvent",
    "EntityState",
    "EventBus",
    "Neighbor",
    "NeighborReportEvent",
    "StateChangedEvent",
    "is_control",
]
