from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription


@dataclass
class AssertMutualWatchPartnerService:
    """Ensures watch_with_user_id refers to an existing mutual subscription partner."""

    _session: AsyncSession

    class WatchWithUserNotFoundError(Exception):
        pass

    class NotMutualWatchPartnerError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        watch_with_user_id: UUID,
    ) -> None:
        if watch_with_user_id == actor_user_id:
            raise self.NotMutualWatchPartnerError

        partner = await self._session.get(User, watch_with_user_id)
        if partner is None:
            raise self.WatchWithUserNotFoundError

        actor_follows = (
            await self._session.execute(
                select(UserSubscription.id).where(
                    UserSubscription.follower_user_id == actor_user_id,
                    UserSubscription.following_user_id == watch_with_user_id,
                )
            )
        ).scalar_one_or_none()
        partner_follows = (
            await self._session.execute(
                select(UserSubscription.id).where(
                    UserSubscription.follower_user_id == watch_with_user_id,
                    UserSubscription.following_user_id == actor_user_id,
                )
            )
        ).scalar_one_or_none()
        if actor_follows is None or partner_follows is None:
            raise self.NotMutualWatchPartnerError
