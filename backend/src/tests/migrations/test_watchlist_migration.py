from __future__ import annotations

import importlib

import pytest


def test_legacy_watchlist_migration_creates_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = importlib.import_module('migrations.versions.w1x2y3z4a02_migrate_watchlist_films')

    statements: list[str] = []

    def _capture(sql: str) -> None:
        statements.append(sql)

    monkeypatch.setattr(migration.op, 'execute', _capture)

    migration.upgrade()

    assert any('INSERT INTO watchlist_entry' in stmt for stmt in statements)
    assert any('FROM user_watchlist_film' in stmt for stmt in statements)
    assert any('ON CONFLICT' in stmt for stmt in statements)


def test_drop_legacy_watchlist_table_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = importlib.import_module(
        'migrations.versions.w1x2y3z4a03_drop_user_watchlist_film'
    )

    statements: list[str] = []

    def _capture(sql: str) -> None:
        statements.append(sql)

    monkeypatch.setattr(migration.op, 'execute', _capture)

    migration.upgrade()

    assert any('DROP TABLE IF EXISTS user_watchlist_film' in stmt for stmt in statements)
