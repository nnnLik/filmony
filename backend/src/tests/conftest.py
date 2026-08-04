from __future__ import annotations

import os
from typing import Any

os.environ['ENV'] = 'test'
os.environ.setdefault('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/15')
os.environ.setdefault('TMDB_API_KEY', 'ci-placeholder-key')

from tests.support.xdist_bootstrap import apply_worker_schema_env

apply_worker_schema_env()

from conf.settings import AppEnv, settings

settings.app.ENV = AppEnv.TEST

pytest_plugins = ('tests.support.plugins',)


def pytest_configure(config: Any) -> None:
    """Select the xdist worker schema after pytest sets its worker identity."""
    del config
    apply_worker_schema_env()
