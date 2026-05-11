from __future__ import annotations

from conf import settings
from core.database import get_engine
from models import Base


def _require_test_env() -> None:
    if not settings.app.is_test:
        raise RuntimeError('Refusing to manage tables outside test environment (ENV must be test).')


async def create_all_tables() -> None:
    _require_test_env()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    _require_test_env()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
