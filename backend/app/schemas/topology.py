"""拓扑图的出参。"""

from datetime import datetime

from pydantic import BaseModel


class TopologyNode(BaseModel):
    id: str
    kind: str
    """device / neighbor"""

    name: str
    category: str | None = None

    mac: str | None = None
    ip: str | None = None
    hostname: str | None = None

    available: bool | None = None
    device_id: str | None = None


class TopologyEdge(BaseModel):
    source: str
    target: str

    interface: str | None = None
    is_wireless: bool = False
    discovery_source: str
    last_seen_at: datetime


class TopologyResponse(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    generated_at: datetime
    active_within_seconds: int
