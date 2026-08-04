from __future__ import annotations

import os

import pytest

from tests.support.xdist_bootstrap import apply_worker_schema_env, worker_schema_name


def test_worker_schema_name_none_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('PYTEST_XDIST_WORKER', raising=False)
    assert worker_schema_name(None) == 'pytest_master'


def test_worker_schema_name_master() -> None:
    assert worker_schema_name('master') == 'pytest_master'


def test_worker_schema_name_gw0() -> None:
    assert worker_schema_name('gw0') == 'pytest_gw0'


def test_apply_worker_schema_env_sets_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('PYTEST_DB_SCHEMA', raising=False)
    monkeypatch.delenv('PYTEST_XDIST_WORKER', raising=False)
    schema = apply_worker_schema_env()
    assert schema == 'pytest_master'
    assert os.environ['PYTEST_DB_SCHEMA'] == 'pytest_master'
