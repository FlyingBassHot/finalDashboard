import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# 让测试无需安装即可从 backend/ 根目录导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: E402,F401  注册全部 ORM 模型
from app.core.database import Base  # noqa: E402

SessionFactory = async_sessionmaker[AsyncSession]


@pytest.fixture()
async def session_factory(tmp_path) -> AsyncIterator[SessionFactory]:
    """每个测试一个独立的临时 SQLite 文件。"""

    url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    yield factory

    await engine.dispose()
