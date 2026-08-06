from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.user_achievement import UserAchievement
from models.user_achievement_pin import MAX_ACHIEVEMENT_PINS, UserAchievementPin


@dataclass
class SetUserAchievementPinsService:
    """Replace profile achievement pins with an ordered list (max 3 unlocked slugs)."""

    _session: AsyncSession

    class AchievementNotFound(Exception):
        pass

    class AchievementNotUnlocked(Exception):
        pass

    class TooManyPins(Exception):
        pass

    class DuplicateSlug(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, achievement_slugs: list[str]) -> None:
        normalized = [slug.strip() for slug in achievement_slugs if slug.strip() != '']
        if len(normalized) > MAX_ACHIEVEMENT_PINS:
            raise self.TooManyPins
        if len(set(normalized)) != len(normalized):
            raise self.DuplicateSlug

        if not normalized:
            await self._session.execute(
                delete(UserAchievementPin).where(UserAchievementPin.user_id == user_id)
            )
            await self._session.commit()
            return

        achievements = list(
            (
                await self._session.execute(
                    select(Achievement).where(Achievement.slug.in_(normalized))
                )
            )
            .scalars()
            .all()
        )
        achievement_by_slug = {achievement.slug: achievement for achievement in achievements}
        missing = [slug for slug in normalized if slug not in achievement_by_slug]
        if missing:
            raise self.AchievementNotFound

        achievement_ids = [int(achievement_by_slug[slug].id) for slug in normalized]
        unlocked_ids = set(
            (
                await self._session.execute(
                    select(UserAchievement.achievement_id).where(
                        UserAchievement.user_id == user_id,
                        UserAchievement.achievement_id.in_(achievement_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        if len(unlocked_ids) != len(achievement_ids):
            raise self.AchievementNotUnlocked

        await self._session.execute(
            delete(UserAchievementPin).where(UserAchievementPin.user_id == user_id)
        )
        for slot_index, slug in enumerate(normalized):
            achievement = achievement_by_slug[slug]
            self._session.add(
                UserAchievementPin(
                    user_id=user_id,
                    achievement_id=int(achievement.id),
                    slot_index=slot_index,
                )
            )
        await self._session.commit()
