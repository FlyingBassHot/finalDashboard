"""邻居关系的数据访问层。"""

import re
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.topology import Neighbor
from app.models.neighbor_link import NeighborLink

MAC_PATTERN = re.compile(r"[0-9a-f]{2}(:[0-9a-f]{2}){5}")


def normalize_mac(value: str) -> str | None:
    mac = value.strip().lower().replace("-", ":")

    return mac if MAC_PATTERN.fullmatch(mac) else None


class NeighborLinkRepository:
    async def upsert_many(
        self,
        db: AsyncSession,
        device_id: str,
        neighbors: Sequence[Neighbor],
        observed_at: datetime,
    ) -> None:
        result = await db.execute(
            select(NeighborLink).where(
                NeighborLink.device_id == device_id,
            ),
        )
        existing = {row.mac: row for row in result.scalars().all()}

        for neighbor in neighbors:
            mac = normalize_mac(neighbor.mac)

            if mac is None:
                continue

            row = existing.get(mac)

            if row is None:
                row = NeighborLink(
                    device_id=device_id,
                    mac=mac,
                    first_seen_at=observed_at,
                    last_seen_at=observed_at,
                )
                db.add(row)
                existing[mac] = row

            row.ip = neighbor.ip
            row.hostname = neighbor.hostname
            row.interface = neighbor.interface
            row.source = neighbor.source
            row.is_wireless = neighbor.is_wireless
            row.last_seen_at = observed_at

        await db.flush()

    async def list_active(
        self,
        db: AsyncSession,
        since: datetime,
    ) -> list[NeighborLink]:
        result = await db.execute(
            select(NeighborLink)
            .where(NeighborLink.last_seen_at >= since)
            .order_by(NeighborLink.device_id, NeighborLink.mac),
        )

        return list(result.scalars().all())

    async def list_for_device(
        self,
        db: AsyncSession,
        device_id: str,
    ) -> list[NeighborLink]:
        result = await db.execute(
            select(NeighborLink)
            .where(NeighborLink.device_id == device_id)
            .order_by(NeighborLink.mac),
        )

        return list(result.scalars().all())

    async def delete_stale(
        self,
        db: AsyncSession,
        cutoff: datetime,
    ) -> int:
        result = await db.execute(
            delete(NeighborLink).where(
                NeighborLink.last_seen_at < cutoff,
            ),
        )

        return result.rowcount or 0

    async def delete_for_devices(
        self,
        db: AsyncSession,
        device_ids: Sequence[str],
    ) -> int:
        if not device_ids:
            return 0

        result = await db.execute(
            delete(NeighborLink).where(
                NeighborLink.device_id.in_(device_ids),
            ),
        )

        return result.rowcount or 0
