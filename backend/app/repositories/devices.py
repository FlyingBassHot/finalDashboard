"""设备持久化。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_types import utcnow
from app.domain.device import DeviceDescriptor
from app.models.device import Device


class DeviceRepository:
    async def upsert(
        self,
        db: AsyncSession,
        device: DeviceDescriptor,
        available: bool | None = None,
    ) -> Device:
        row = await db.get(Device, device.device_id)

        if row is None:
            row = Device(device_id=device.device_id)
            db.add(row)

        row.integration = device.integration
        row.instance_name = device.instance
        row.device_key = device.key
        row.identity = device.identity
        row.name = device.name
        row.category = device.category.value
        row.manufacturer = device.manufacturer
        row.model = device.model
        row.sw_version = device.sw_version

        if available is not None:
            row.available = available

        row.updated_at = utcnow()

        await db.flush()

        return row

    async def get(
        self,
        db: AsyncSession,
        device_id: str,
    ) -> Device | None:
        return await db.get(Device, device_id)

    async def list(
        self,
        db: AsyncSession,
        integration: str | None = None,
        instance_name: str | None = None,
    ) -> list[Device]:
        statement = select(Device).order_by(Device.device_id)

        if integration is not None:
            statement = statement.where(Device.integration == integration)

        if instance_name is not None:
            statement = statement.where(
                Device.instance_name == instance_name,
            )

        result = await db.execute(statement)

        return list(result.scalars().all())

    async def delete_by_instance(
        self,
        db: AsyncSession,
        integration: str,
        instance_name: str,
    ) -> None:
        await db.execute(
            delete(Device).where(
                Device.integration == integration,
                Device.instance_name == instance_name,
            ),
        )

    async def set_availability(
        self,
        db: AsyncSession,
        device_id: str,
        available: bool,
    ) -> None:
        row = await db.get(Device, device_id)

        if row is None:
            return

        row.available = available
        row.last_seen_at = utcnow()
        row.updated_at = utcnow()

        await db.flush()
