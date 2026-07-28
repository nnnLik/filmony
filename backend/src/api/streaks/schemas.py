from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

STREAK_BATCH_MAX_IDS = 100
STREAK_BATCH_MIN_CURRENT = 4


class StreakBatchRequest(BaseModel):
    user_ids: list[UUID] = Field(default_factory=list, max_length=STREAK_BATCH_MAX_IDS)


class StreakItemResponse(BaseModel):
    current: int


class StreakBatchResponse(BaseModel):
    items: dict[str, StreakItemResponse]


class MyStreakResponse(BaseModel):
    current: int
