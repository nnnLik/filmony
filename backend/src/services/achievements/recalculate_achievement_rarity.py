from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.user_achievement import UserAchievement
from models.user_card import UserCard
from services.achievements.rarity_math import compute_rarity_percent
from services.collections.meaningful_rated_card import meaningful_rated_card_criteria


@dataclass
class RecalculateAchievementRarityService:
    """Recompute global rarity snapshots for catalog achievements."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, achievement_id: int | None = None) -> None:
        eligible_users_count = await self._count_eligible_users()
        now = dt.datetime.now(dt.UTC)

        achievements = await self._load_achievements(achievement_id)
        for achievement in achievements:
            holders_count = await self._count_holders(int(achievement.id))
            rarity_percent = compute_rarity_percent(
                holders_count=holders_count,
                eligible_users_count=eligible_users_count,
            )
            await self._session.execute(
                update(Achievement)
                .where(Achievement.id == achievement.id)
                .values(
                    holders_count=holders_count,
                    eligible_users_count=eligible_users_count,
                    rarity_percent=rarity_percent,
                    rarity_calculated_at=now,
                )
            )
        await self._session.commit()

    async def _load_achievements(self, achievement_id: int | None) -> list[Achievement]:
        stmt = select(Achievement)
        if achievement_id is not None:
            stmt = stmt.where(Achievement.id == achievement_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def _count_eligible_users(self) -> int:
        stmt = (
            select(func.count(func.distinct(UserCard.user_id)))
            .select_from(UserCard)
            .where(*meaningful_rated_card_criteria())
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _count_holders(self, achievement_id: int) -> int:
        stmt = (
            select(func.count(func.distinct(UserAchievement.user_id)))
            .select_from(UserAchievement)
            .where(UserAchievement.achievement_id == achievement_id)
        )
        return int((await self._session.execute(stmt)).scalar_one())
