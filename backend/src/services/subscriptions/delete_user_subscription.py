from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription


class TargetUserNotFoundError(Exception):
    pass


class SubscriptionNotFoundError(Exception):
    pass


class DeleteUserSubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, viewer_user_id: UUID, target_user_id: UUID) -> None:
        target = await self._session.execute(select(User.id).where(User.id == target_user_id))
        if target.scalar_one_or_none() is None:
            raise TargetUserNotFoundError

        stmt = delete(UserSubscription).where(
            UserSubscription.follower_user_id == viewer_user_id,
            UserSubscription.following_user_id == target_user_id,
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            await self._session.rollback()
            raise SubscriptionNotFoundError

        await self._session.commit()
