from __future__ import annotations

from collections.abc import AsyncGenerator
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


def _connect_args() -> dict[str, str] | None:
    if settings.app.is_test:
        sch = settings.database.test_schema
        return {"server_settings": {"search_path": f"{sch}, public"}}
    sch = settings.database.default_schema
    if sch != "public":
        return {"server_settings": {"search_path": f"{sch}, public"}}
    return None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        kwargs: dict[str, Any] = {
            "echo": settings.database.echo,
            "pool_pre_ping": True,
        }
        ca = _connect_args()
        if ca is not None:
            kwargs["connect_args"] = ca
        _engine = create_async_engine(
            settings.database.async_sqlalchemy_url,
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
