from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from conf import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _normalize_async_sqlalchemy_url(raw: str) -> str:
    u = raw.strip()
    if u.startswith('postgresql+asyncpg://'):
        return u
    if u.startswith('postgresql://'):
        return 'postgresql+asyncpg://' + u.removeprefix('postgresql://')
    return u


def async_engine_connect_url() -> str:
    if settings.app.is_test:
        tu = settings.database.test_url
        if not (tu and str(tu).strip()):
            raise RuntimeError('DATABASE_TEST_URL is not set')
        return _normalize_async_sqlalchemy_url(str(tu))
    return settings.database.async_sqlalchemy_url


def _test_db_schema() -> str:
    return os.environ.get('PYTEST_DB_SCHEMA', 'pytest_master')


def _connect_args() -> dict[str, str] | None:
    if settings.app.is_test:
        return {
            'server_settings': {'search_path': _test_db_schema()},
        }
    return {
        'server_settings': {'search_path': 'public'},
    }


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        kwargs: dict[str, Any] = {
            'echo': settings.database.echo,
            'pool_pre_ping': True,
        }
        ca = _connect_args()
        if ca is not None:
            kwargs['connect_args'] = ca
        _engine = create_async_engine(
            async_engine_connect_url(),
            **kwargs,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def disposable_async_session() -> AsyncGenerator[AsyncSession]:
    """Celery engagement tasks run ``asyncio.run`` in a worker thread (different loop than FastAPI).

    Each call uses a dedicated short-lived engine so asyncpg connections stay bound to that loop.
    Follow-up: pool-per-loop (keyed by ``id(asyncio.get_running_loop())``) to cut churn in hot paths.
    """

    kwargs: dict[str, Any] = {
        'echo': settings.database.echo,
        'pool_pre_ping': True,
    }
    ca = _connect_args()
    if ca is not None:
        kwargs['connect_args'] = ca
    engine = create_async_engine(
        async_engine_connect_url(),
        **kwargs,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
