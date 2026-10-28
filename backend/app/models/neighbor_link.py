"""邻居关系（按设备 + MAC 聚合，保留最近可见时间）。

与原始报文不同，这里一个 (device_id, mac) 只保留一行：
- 每次上报更新 last_seen_at 与字段；
- 拓扑读取只看最近活跃窗口；
- 超过保留期由清理任务删除。
"""

from datetime import datetime

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.db_types import UTCDateTime


class NeighborLink(Base):
    __tablename__ = "neighbor_links"

    device_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    """父设备（上报邻居的设备）。"""

    mac: Mapped[str] = mapped_column(String(17), primary_key=True)

    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(200), nullable=True)
    interface: Mapped[str | None] = mapped_column(String(64), nullable=True)

    source: Mapped[str] = mapped_column(
        String(32),
        default="arp",
        nullable=False,
    )
    is_wireless: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )

    __table_args__ = (Index("ix_neighbor_links_last_seen", "last_seen_at"),)
