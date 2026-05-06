from __future__ import annotations

import pytest

from conf.settings import AppEnv, settings
from tests.support import db_setup


class _DummyConnection:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.run_sync_called = False

    async def execute(self, statement: object) -> None:
        self.executed.append(str(statement))

    async def run_sync(self, _: object) -> None:
        self.run_sync_called = True


class _DummyBeginContext:
    def __init__(self, conn: _DummyConnection) -> None:
        self._conn = conn

    async def __aenter__(self) -> _DummyConnection:
        return self._conn

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None


class _DummyEngine:
    def __init__(self, conn: _DummyConnection) -> None:
        self._conn = conn

    def begin(self) -> _DummyBeginContext:
        return _DummyBeginContext(self._conn)


@pytest.mark.asyncio
async def test_ensure_test_schema_rejects_non_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.DEV)

    with pytest.raises(RuntimeError, match='outside test environment'):
        await db_setup.ensure_test_schema()


@pytest.mark.asyncio
async def test_drop_all_tables_rejects_non_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.DEV)

    with pytest.raises(RuntimeError, match='outside test environment'):
        await db_setup.drop_all_tables()


@pytest.mark.asyncio
async def test_ensure_test_schema_rejects_public_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.TEST)
    monkeypatch.setattr(settings.database, 'default_schema', 'app')
    monkeypatch.setattr(settings.database, 'test_schema', 'public')

    with pytest.raises(RuntimeError, match='public schema'):
        await db_setup.ensure_test_schema()


@pytest.mark.asyncio
async def test_ensure_test_schema_rejects_same_default_and_test_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.TEST)
    monkeypatch.setattr(settings.database, 'default_schema', 'kino')
    monkeypatch.setattr(settings.database, 'test_schema', 'kino')

    with pytest.raises(RuntimeError, match='equal to DATABASE_SCHEMA'):
        await db_setup.ensure_test_schema()


@pytest.mark.asyncio
async def test_ensure_test_schema_creates_schema_when_configuration_is_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.TEST)
    monkeypatch.setattr(settings.database, 'default_schema', 'public')
    monkeypatch.setattr(settings.database, 'test_schema', 'filmony_test')

    conn = _DummyConnection()
    engine = _DummyEngine(conn)
    monkeypatch.setattr(db_setup, 'get_engine', lambda: engine)

    await db_setup.ensure_test_schema()

    assert conn.executed
    assert 'CREATE SCHEMA IF NOT EXISTS filmony_test' in conn.executed[0]
