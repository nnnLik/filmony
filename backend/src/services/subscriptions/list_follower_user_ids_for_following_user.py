"""Resolve follower user ids for a publisher (`UserSubscription.following_user_id`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_subscription import UserSubscription


@dataclass
class ListFollowerUserIdsForFollowingUserService:
    """Lists distinct users who follow ``following_user_id``, optionally excluding a set."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        following_user_id: UUID,
        *,
        exclude_user_ids: frozenset[UUID] | None = None,
    ) -> tuple[UUID, ...]:
        stmt = (
            select(UserSubscription.follower_user_id)
            .where(UserSubscription.following_user_id == following_user_id)
            .order_by(UserSubscription.follower_user_id.asc())
        )
        if exclude_user_ids:
            stmt = stmt.where(UserSubscription.follower_user_id.notin_(exclude_user_ids))
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(dict.fromkeys(rows))
