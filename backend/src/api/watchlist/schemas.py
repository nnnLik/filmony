from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.card_enums import CardCompany


class WatchTag(StrEnum):
    watch_later = 'watch_later'


class WatchlistEntryCreate(BaseModel):
    card_id: str = Field(..., min_length=1, max_length=128)
    provider_meta: dict
    watch_tag: WatchTag
    company: CardCompany = CardCompany.alone
    category_id: int | None = Field(default=None, ge=1)
    watch_note: str = Field(default='', max_length=500)
    watch_with_user_id: UUID | None = None
    watch_with_user_ids: list[UUID] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra='forbid')

    @field_validator('watch_with_user_ids')
    @classmethod
    def _validate_partner_count(cls, value: list[UUID]) -> list[UUID]:
        if len(value) > 20:
            raise ValueError('max 20 watch partners allowed')
        return value


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
    watch_with_user_ids: list[UUID] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')
