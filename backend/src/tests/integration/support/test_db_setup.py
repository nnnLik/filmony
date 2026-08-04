from __future__ import annotations

import pytest

from conf.settings import AppEnv, settings
from tests.support import db_setup


class _DummyConnection:
    def __init__(self) -> None:
        self.run_sync_called = False

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
async def test_drop_all_tables_rejects_non_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.DEV)

    with pytest.raises(RuntimeError, match='outside test environment'):
        await db_setup.drop_all_tables()


@pytest.mark.asyncio
async def test_create_all_tables_rejects_non_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.DEV)

    with pytest.raises(RuntimeError, match='outside test environment'):
        await db_setup.create_all_tables()


@pytest.mark.asyncio
async def test_drop_all_tables_runs_metadata_drop_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.app, 'ENV', AppEnv.TEST)

    conn = _DummyConnection()
    engine = _DummyEngine(conn)
    monkeypatch.setattr(db_setup, 'get_engine', lambda: engine)

    await db_setup.drop_all_tables()

    assert conn.run_sync_called
