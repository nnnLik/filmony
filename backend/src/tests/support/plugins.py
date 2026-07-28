"""Фикстуры pytest: клиент, подготовка БД."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import dispose_engine
from services.feed.global_feed_head_broker import reset_global_feed_head_broker_for_tests
from tests.support import db_setup
from utils.app_utils import get_app, setup_app


def pytest_sessionstart(session: pytest.Session) -> None:
    del session

    async def _bootstrap_worker_schema() -> None:
        await db_setup.ensure_schema_exists()
        await dispose_engine()

    asyncio.run(_bootstrap_worker_schema())


@pytest_asyncio.fixture
async def prepare_db() -> None:
    reset_global_feed_head_broker_for_tests()
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
