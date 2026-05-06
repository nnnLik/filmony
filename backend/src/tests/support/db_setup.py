"""Подготовка БД для pytest: схема, create_all / drop_all."""

from __future__ import annotations

from sqlalchemy import text

from conf import settings
from core.database import get_engine
from models import Base


async def ensure_test_schema() -> None:
    schema = settings.database.test_schema
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


async def create_all_tables() -> None:
    await ensure_test_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
