from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.user_achievement_pin import MAX_ACHIEVEMENT_PINS
from services.achievements.list_pinned_achievements import PinnedAchievementDTO
from services.achievements.list_user_achievements import UserAchievementItemDTO


class AchievementItemResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    icon_key: str | None
    collection_slug: str
    unlocked: bool
    unlocked_at: dt.datetime | None
    holders_count: int
    eligible_users_count: int
    rarity_percent: float | None
    rarity_calculated_at: dt.datetime | None
    is_pinned: bool
    pin_slot_index: int | None

    model_config = ConfigDict(extra='forbid')


class MyAchievementsListResponse(BaseModel):
    items: list[AchievementItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class SetAchievementPinsRequest(BaseModel):
    achievement_slugs: list[str] = Field(default_factory=list, max_length=MAX_ACHIEVEMENT_PINS)

    model_config = ConfigDict(extra='forbid')

    @field_validator('achievement_slugs')
    @classmethod
    def _validate_slugs(cls, value: list[str]) -> list[str]:
        if len(value) > MAX_ACHIEVEMENT_PINS:
            raise ValueError(f'max {MAX_ACHIEVEMENT_PINS} achievement pins allowed')
        return value


class PinnedAchievementResponse(BaseModel):
    slug: str
    title: str
    description: str | None
    icon_key: str | None
    collection_slug: str
    unlocked_at: dt.datetime
    holders_count: int
    eligible_users_count: int
    rarity_percent: float | None
    rarity_calculated_at: dt.datetime | None
    slot_index: int

    model_config = ConfigDict(extra='forbid')


def build_achievement_item_response(dto: UserAchievementItemDTO) -> AchievementItemResponse:
    return AchievementItemResponse(
        slug=dto.slug,
        title=dto.title,
        description=dto.description,
        icon_key=dto.icon_key,
        collection_slug=dto.collection_slug,
        unlocked=dto.unlocked,
        unlocked_at=dto.unlocked_at,
        holders_count=dto.holders_count,
        eligible_users_count=dto.eligible_users_count,
        rarity_percent=dto.rarity_percent,
        rarity_calculated_at=dto.rarity_calculated_at,
        is_pinned=dto.is_pinned,
        pin_slot_index=dto.pin_slot_index,
    )


def build_my_achievements_list_response(
    items: list[UserAchievementItemDTO],
) -> MyAchievementsListResponse:
    return MyAchievementsListResponse(
        items=[build_achievement_item_response(item) for item in items],
    )


def build_pinned_achievement_response(dto: PinnedAchievementDTO) -> PinnedAchievementResponse:
    return PinnedAchievementResponse(
        slug=dto.slug,
        title=dto.title,
        description=dto.description,
        icon_key=dto.icon_key,
        collection_slug=dto.collection_slug,
        unlocked_at=dto.unlocked_at,
        holders_count=dto.holders_count,
        eligible_users_count=dto.eligible_users_count,
        rarity_percent=dto.rarity_percent,
        rarity_calculated_at=dto.rarity_calculated_at,
        slot_index=dto.slot_index,
    )
