"""Per-worker PostgreSQL schema selection for pytest-xdist."""

from __future__ import annotations

import os


def worker_schema_name(worker_id: str | None = None) -> str:
    wid = worker_id if worker_id is not None else os.environ.get('PYTEST_XDIST_WORKER')
    if not wid or wid == 'master':
        return 'pytest_master'
    return f'pytest_{wid}'


def apply_worker_schema_env() -> str:
    schema = worker_schema_name()
    os.environ['PYTEST_DB_SCHEMA'] = schema
    return schema
