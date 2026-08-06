from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.user_achievement import UserAchievement

logger = logging.getLogger(__name__)


@dataclass
class GrantCollectionAchievementService:
    """Grant a sticky collection-completion achievement when a user finishes a curated list.

    Idempotent: safe to call on every progress recompute at 100%. Once unlocked, the row
    is never deleted when ratings or progress drop.
    """

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, collection_slug: str) -> None:
        achievement = (
            await self._session.execute(
                select(Achievement).where(Achievement.collection_slug == collection_slug)
            )
        ).scalar_one_or_none()
        if achievement is None:
            logger.warning(
                'GrantCollectionAchievementService: no achievement for collection_slug=%s',
                collection_slug,
            )
            return

        achievement_id = int(achievement.id)
        now = dt.datetime.now(dt.UTC)
        stmt = (
            pg_insert(UserAchievement)
            .values(
                user_id=user_id,
                achievement_id=achievement_id,
                unlocked_at=now,
            )
            .on_conflict_do_nothing(index_elements=['user_id', 'achievement_id'])
        )
        await self._session.execute(stmt)
