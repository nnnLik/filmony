from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.user_achievement import UserAchievement
from models.user_achievement_pin import UserAchievementPin


@dataclass(frozen=True, slots=True)
class PinnedAchievementDTO:
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


@dataclass
class ListPinnedAchievementsService:
    """Return ordered pinned achievements for a user's public profile."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[PinnedAchievementDTO]:
        rows = (
            await self._session.execute(
                select(UserAchievementPin, Achievement, UserAchievement)
                .join(Achievement, Achievement.id == UserAchievementPin.achievement_id)
                .join(
                    UserAchievement,
                    (UserAchievement.user_id == UserAchievementPin.user_id)
                    & (UserAchievement.achievement_id == UserAchievementPin.achievement_id),
                )
                .where(UserAchievementPin.user_id == user_id)
                .order_by(UserAchievementPin.slot_index)
            )
        ).all()

        return [
            PinnedAchievementDTO(
                slug=achievement.slug,
                title=achievement.title,
                description=achievement.description,
                icon_key=achievement.icon_key,
                collection_slug=achievement.collection_slug,
                unlocked_at=user_achievement.unlocked_at,
                holders_count=int(achievement.holders_count),
                eligible_users_count=int(achievement.eligible_users_count),
                rarity_percent=float(achievement.rarity_percent)
                if achievement.rarity_percent is not None
                else None,
                rarity_calculated_at=achievement.rarity_calculated_at,
                slot_index=int(pin.slot_index),
            )
            for pin, achievement, user_achievement in rows
        ]
