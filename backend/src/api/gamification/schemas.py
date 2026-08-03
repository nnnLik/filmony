from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PassportStampResponse(BaseModel):
    stamp_id: str
    title: str
    description: str
    unlocked: bool
    unlocked_at: datetime | None = None
    progress_current: int | None = None
    progress_target: int | None = None
    unlock_card_id: int | None = None
    unlock_film_title: str | None = None
    unlock_film_poster_url: str | None = None

    model_config = ConfigDict(extra='forbid')


class PassportResponse(BaseModel):
    stamps: list[PassportStampResponse] = Field(default_factory=list)
    unlocked_count: int = 0

    model_config = ConfigDict(extra='forbid')


class MarathonAchievementResponse(BaseModel):
    kind: str
    key: str
    label: str
    count: int
    unlocked_at: datetime
    sample_poster_urls: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class ShelfPhysicsResponse(BaseModel):
    mode: str
    streak_length: int

    model_config = ConfigDict(extra='forbid')


class GamificationResponse(BaseModel):
    passport: PassportResponse
    marathons: list[MarathonAchievementResponse] = Field(default_factory=list)
    shelf_physics: ShelfPhysicsResponse

    model_config = ConfigDict(extra='forbid')


class PublicPassportResponse(BaseModel):
    stamps: list[PassportStampResponse] = Field(default_factory=list)
    unlocked_count: int = 0

    model_config = ConfigDict(extra='forbid')


class RatedDirectorItemResponse(BaseModel):
    kinopoisk_id: int
    name: str
    count: int

    model_config = ConfigDict(extra='forbid')


class RatedDirectorsListResponse(BaseModel):
    items: list[RatedDirectorItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')
