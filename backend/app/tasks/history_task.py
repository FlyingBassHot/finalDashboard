"""历史与邻居数据的保留期清理。"""

import logging
from datetime import timedelta

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.db_types import utcnow
from app.history.repository import HistoryRepository
from app.topology.repository import NeighborLinkRepository

logger = logging.getLogger(__name__)


async def cleanup_history_task() -> None:
    cutoff = utcnow() - timedelta(days=settings.history_retention_days)

    async with AsyncSessionLocal() as db:
        try:
            deleted_history = await HistoryRepository().delete_before(
                db,
                cutoff,
            )
            deleted_neighbors = await NeighborLinkRepository().delete_stale(
                db,
                cutoff,
            )
            await db.commit()

        except Exception:
            await db.rollback()
            logger.warning("history cleanup failed", exc_info=True)
            return

    logger.info(
        "history cleanup: %s samples, %s neighbor links removed",
        deleted_history,
        deleted_neighbors,
    )
