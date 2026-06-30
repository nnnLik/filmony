from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WatchTag(StrEnum):
    watch_later = 'watch_later'


class WatchlistEntryCreate(BaseModel):
    card_id: str = Field(..., min_length=1, max_length=128)
    provider_meta: dict
    watch_tag: WatchTag
    watch_with_user_id: UUID | None = None

    model_config = ConfigDict(extra='forbid')


class WatchlistEntryUpdate(BaseModel):
    watch_tag: WatchTag

    model_config = ConfigDict(extra='forbid')


class WatchlistEntryResponse(BaseModel):
    id: int
    user_id: UUID
    card_id: str
    provider_meta: dict
    watch_tag: str
    watch_with_user_id: UUID | None

    model_config = ConfigDict(extra='forbid')
