from __future__ import annotations

from enum import StrEnum


class TasteQuizSessionStatus(StrEnum):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'
