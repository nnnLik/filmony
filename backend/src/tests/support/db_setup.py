"""Подготовка БД для pytest: схема, create_all / drop_all."""

from __future__ import annotations

from sqlalchemy import text

from conf import settings
from core.database import get_engine
from models import Base


def _ensure_safe_test_database() -> None:
    if not settings.app.is_test:
        raise RuntimeError('Refusing to manage tables outside test environment (ENV must be test).')

    test_schema = settings.database.test_schema
    if test_schema == 'public':
        raise RuntimeError('Refusing to use public schema as DATABASE_TEST_SCHEMA.')

    if test_schema == settings.database.default_schema:
        raise RuntimeError(
            'Refusing to use DATABASE_TEST_SCHEMA equal to DATABASE_SCHEMA.',
        )


async def ensure_test_schema() -> None:
    _ensure_safe_test_database()
    schema = settings.database.test_schema
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))


async def create_all_tables() -> None:
    _ensure_safe_test_database()
    await ensure_test_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    _ensure_safe_test_database()
    # PostgreSQL skips non-existent schemas in search_path; if `filmony_test` is not
    # created yet, unqualified DROP targets `public` and wipes the real database.
    await ensure_test_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
