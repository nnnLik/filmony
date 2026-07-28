from __future__ import annotations

from enum import Enum


class WatchSessionStatus(str, Enum):
    planned = 'planned'
    done = 'done'
