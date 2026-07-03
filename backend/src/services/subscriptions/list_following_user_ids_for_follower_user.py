"""Resolve following user ids for a subscriber (`UserSubscription.follower_user_id`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_subscription import UserSubscription


@dataclass
class ListFollowingUserIdsForFollowerUserService:
    """Lists distinct users that ``follower_user_id`` follows."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, follower_user_id: UUID) -> tuple[UUID, ...]:
        stmt = (
            select(UserSubscription.following_user_id)
            .where(UserSubscription.follower_user_id == follower_user_id)
            .order_by(UserSubscription.following_user_id.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(dict.fromkeys(rows))
