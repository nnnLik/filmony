from __future__ import annotations

from enum import Enum, StrEnum


class WatchSessionStatus(StrEnum):
    planned = 'planned'
    done = 'done'
