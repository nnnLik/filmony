from __future__ import annotations

import os

from sqlalchemy import text

from conf import settings
from core.database import get_engine
from models import Base


def _require_test_env() -> None:
    if not settings.app.is_test:
        raise RuntimeError('Refusing to manage tables outside test environment (ENV must be test).')


def _worker_schema() -> str:
    return os.environ.get('PYTEST_DB_SCHEMA', 'pytest_master')


async def ensure_schema_exists() -> None:
    _require_test_env()
    schema = _worker_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))


async def create_all_tables() -> None:
    _require_test_env()
    await ensure_schema_exists()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    _require_test_env()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
