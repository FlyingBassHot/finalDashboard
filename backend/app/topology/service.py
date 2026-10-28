"""拓扑图构建：把邻居关系归并成节点 + 边。"""

from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.repositories.devices import DeviceRepository
from app.topology.repository import (
    NeighborLinkRepository,
    normalize_mac,
)

MAC_PREFIX = "mac:"


def _mac_from_identity(identity: str | None) -> str | None:
    if not identity:
        return None

    value = identity.strip().lower()

    if value.startswith(MAC_PREFIX):
        value = value[len(MAC_PREFIX) :]

    return normalize_mac(value)


class TopologyService:
    def __init__(self) -> None:
        self.links = NeighborLinkRepository()
        self.devices = DeviceRepository()

    async def build(
        self,
        db: AsyncSession,
        *,
        active_within_seconds: int = 600,
    ) -> dict[str, Any]:
        since = utcnow() - timedelta(
            seconds=max(1, active_within_seconds),
        )

        links = await self.links.list_active(db, since)
        devices = await self.devices.list(db)

        nodes: dict[str, dict[str, Any]] = {}
        mac_to_device: dict[str, str] = {}

        for device in devices:
            mac = _mac_from_identity(device.identity)

            nodes[device.device_id] = {
                "id": device.device_id,
                "kind": "device",
                "name": device.name,
                "category": device.category,
                "mac": mac,
                "ip": None,
                "hostname": None,
                "available": device.available,
                "device_id": device.device_id,
            }

            if mac is not None:
                mac_to_device[mac] = device.device_id

        edges: dict[tuple[str, str], dict[str, Any]] = {}

        for link in links:
            target = mac_to_device.get(link.mac)

            if target is None:
                target = f"{MAC_PREFIX}{link.mac}"

            if target == link.device_id:
                continue

            target_node = nodes.get(target)

            if target_node is None:
                target_node = {
                    "id": target,
                    "kind": "neighbor",
                    "name": link.hostname or link.mac,
                    "category": None,
                    "mac": link.mac,
                    "ip": link.ip,
                    "hostname": link.hostname,
                    "available": None,
                    "device_id": None,
                }
                nodes[target] = target_node

            else:
                if target_node.get("ip") is None:
                    target_node["ip"] = link.ip

                if target_node.get("hostname") is None:
                    target_node["hostname"] = link.hostname

            if link.device_id not in nodes:
                nodes[link.device_id] = {
                    "id": link.device_id,
                    "kind": "device",
                    "name": link.device_id,
                    "category": "unknown",
                    "mac": None,
                    "ip": None,
                    "hostname": None,
                    "available": None,
                    "device_id": link.device_id,
                }

            key = (link.device_id, target)
            current = edges.get(key)

            # 同一对设备多条链路时优先保留无线信息
            if current is None or (link.is_wireless and not current["is_wireless"]):
                edges[key] = {
                    "source": link.device_id,
                    "target": target,
                    "interface": link.interface,
                    "is_wireless": link.is_wireless,
                    "discovery_source": link.source,
                    "last_seen_at": link.last_seen_at,
                }

        return {
            "nodes": [nodes[key] for key in sorted(nodes)],
            "edges": [edges[key] for key in sorted(edges)],
            "generated_at": utcnow(),
            "active_within_seconds": active_within_seconds,
        }
