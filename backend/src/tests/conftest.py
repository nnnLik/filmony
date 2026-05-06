from __future__ import annotations

import os

os.environ['ENV'] = 'test'

pytest_plugins = ('tests.support.plugins',)
