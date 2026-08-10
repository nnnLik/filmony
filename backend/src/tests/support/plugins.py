"""Фикстуры pytest: клиент, подготовка БД."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.database import dispose_engine
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from services.feed.global_feed_head_broker import reset_global_feed_head_broker_for_tests
from services.kinopoisk.resolve_kinopoisk_film import ResolveKinopoiskFilmService
from services.watch_parties.watch_party_broker import reset_watch_party_broker_for_tests
from services.watch_parties.watch_party_redis import reset_watch_party_redis_for_tests
from tests.support import db_setup
from utils.app_utils import get_app, setup_app


def _collection_needs_db(config: pytest.Config) -> bool:
    """True when the invocation may collect integration tests (Postgres required).

    Unit-only runs (e.g. ``pytest src/tests/unit``) skip schema bootstrap so no DB
    connection is opened. Default collection uses testpaths; if any includes
    ``integration``, bootstrap runs (including under xdist workers).
    """
    cli_roots = [
        str(arg).replace('\\', '/') for arg in config.args if arg and not str(arg).startswith('-')
    ]
    if cli_roots:
        if any('integration' in root for root in cli_roots):
            return True
        return not all('unit' in root for root in cli_roots)

    testpaths = [str(p).replace('\\', '/') for p in (config.getini('testpaths') or [])]
    return any('integration' in path for path in testpaths)


def pytest_sessionstart(session: pytest.Session) -> None:
    if not _collection_needs_db(session.config):
        return

    async def _bootstrap_worker_schema() -> None:
        await db_setup.ensure_schema_exists()
        await dispose_engine()

    asyncio.run(_bootstrap_worker_schema())


@pytest.fixture(autouse=True)
def _noop_film_metadata_sync_on_card_create() -> None:
    """Card create triggers TMDB sync; API tests must not call live TMDB."""
    with patch.object(
        ResolveKinopoiskFilmService,
        'sync_metadata_for_film',
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture(autouse=True)
def _noop_kinopoisk_staff_lookup() -> None:
    """Resolve paths fetch director staff; tests must not call live Kinopoisk."""
    with patch.object(
        KinopoiskProviderTransport,
        'get_staff_by_film_id',
        new_callable=AsyncMock,
        return_value=(),
    ):
        yield


@pytest_asyncio.fixture
async def prepare_db() -> None:
    reset_global_feed_head_broker_for_tests()
    reset_watch_party_broker_for_tests()
    reset_watch_party_redis_for_tests()
    try:
        await db_setup.reset_worker_schema()
        await db_setup.create_all_tables()
        yield
    finally:
        await dispose_engine()
        await db_setup.reset_worker_schema()
        await dispose_engine()


@pytest_asyncio.fixture
async def async_client(prepare_db: None) -> AsyncClient:
    transport = ASGITransport(app=setup_app(get_app()))
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
