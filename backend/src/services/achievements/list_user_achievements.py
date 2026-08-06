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
class UserAchievementItemDTO:
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


@dataclass
class ListUserAchievementsService:
    """Return catalog achievements merged with unlock and pin state for a user."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[UserAchievementItemDTO]:
        achievements = list(
            (await self._session.execute(select(Achievement).order_by(Achievement.slug)))
            .scalars()
            .all()
        )
        if not achievements:
            return []

        achievement_ids = [int(a.id) for a in achievements]
        unlocked_rows = (
            (
                await self._session.execute(
                    select(UserAchievement).where(
                        UserAchievement.user_id == user_id,
                        UserAchievement.achievement_id.in_(achievement_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        unlocked_by_id = {int(row.achievement_id): row for row in unlocked_rows}

        pin_rows = (
            (
                await self._session.execute(
                    select(UserAchievementPin).where(
                        UserAchievementPin.user_id == user_id,
                        UserAchievementPin.achievement_id.in_(achievement_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        pin_by_achievement_id = {int(row.achievement_id): int(row.slot_index) for row in pin_rows}

        return [
            UserAchievementItemDTO(
                slug=achievement.slug,
                title=achievement.title,
                description=achievement.description,
                icon_key=achievement.icon_key,
                collection_slug=achievement.collection_slug,
                unlocked=int(achievement.id) in unlocked_by_id,
                unlocked_at=unlocked_by_id[int(achievement.id)].unlocked_at
                if int(achievement.id) in unlocked_by_id
                else None,
                holders_count=int(achievement.holders_count),
                eligible_users_count=int(achievement.eligible_users_count),
                rarity_percent=float(achievement.rarity_percent)
                if achievement.rarity_percent is not None
                else None,
                rarity_calculated_at=achievement.rarity_calculated_at,
                is_pinned=int(achievement.id) in pin_by_achievement_id,
                pin_slot_index=pin_by_achievement_id.get(int(achievement.id)),
            )
            for achievement in achievements
        ]
