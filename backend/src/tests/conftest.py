from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from conf import settings
from core.database import dispose_engine, get_engine
from models import Base
from utils.app_utils import get_app, setup_app


async def _ensure_test_schema() -> None:
    schema = settings.database.test_schema
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


async def _create_all_tables() -> None:
    await _ensure_test_schema()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_all_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def prepare_db() -> None:
    await _drop_all_tables()
    await _create_all_tables()
    yield
    await _drop_all_tables()
    await dispose_engine()


@pytest_asyncio.fixture
async def async_client(prepare_db: None) -> AsyncClient:
    transport = ASGITransport(app=setup_app(get_app()))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
