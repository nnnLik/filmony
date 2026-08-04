from __future__ import annotations

import os
import re

from sqlalchemy import text

from conf import settings
from core.database import get_engine
from models import Base


def _require_test_env() -> None:
    if not settings.app.is_test:
        raise RuntimeError('Refusing to manage tables outside test environment (ENV must be test).')


def _worker_schema() -> str:
    return os.environ.get('PYTEST_DB_SCHEMA', 'pytest_master')


def _quoted_worker_schema() -> str:
    schema = _worker_schema()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', schema):
        raise RuntimeError(f'Invalid pytest database schema name: {schema!r}')
    return f'"{schema}"'


async def ensure_schema_exists() -> None:
    _require_test_env()
    schema = _quoted_worker_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))


async def reset_worker_schema() -> None:
    """Replace the worker schema without fragile table-by-table FK teardown."""
    _require_test_env()
    schema = _quoted_worker_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
        await conn.execute(text(f'CREATE SCHEMA {schema}'))


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
