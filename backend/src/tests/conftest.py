from __future__ import annotations

import os

os.environ['ENV'] = 'test'

from conf.settings import AppEnv, settings

settings.app.ENV = AppEnv.TEST

pytest_plugins = ('tests.support.plugins',)
