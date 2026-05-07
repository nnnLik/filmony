from __future__ import annotations

import os

os.environ['ENV'] = 'test'
os.environ.setdefault('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/15')

from conf.settings import AppEnv, settings

settings.app.ENV = AppEnv.TEST

pytest_plugins = ('tests.support.plugins',)
