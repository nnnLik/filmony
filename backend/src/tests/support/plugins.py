"""Фикстуры pytest: клиент, подготовка БД."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import dispose_engine
from tests.support import db_setup
from utils.app_utils import get_app, setup_app


@pytest_asyncio.fixture
async def prepare_db() -> None:
    await db_setup.drop_all_tables()
    await db_setup.create_all_tables()
    yield
    await db_setup.drop_all_tables()
    await dispose_engine()


@pytest_asyncio.fixture
async def async_client(prepare_db: None) -> AsyncClient:
    transport = ASGITransport(app=setup_app(get_app()))
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
