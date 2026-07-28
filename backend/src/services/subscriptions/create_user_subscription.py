from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription


class TargetUserNotFoundError(Exception):
    pass


class SelfSubscriptionError(Exception):
    pass


class UserAlreadySubscribedError(Exception):
    pass


class CreateUserSubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, viewer_user_id: UUID, target_user_id: UUID) -> None:
        if viewer_user_id == target_user_id:
            raise SelfSubscriptionError

        target = await self._session.execute(select(User.id).where(User.id == target_user_id))
        if target.scalar_one_or_none() is None:
            raise TargetUserNotFoundError

        entity = UserSubscription(
            follower_user_id=viewer_user_id,
            following_user_id=target_user_id,
        )
        self._session.add(entity)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise UserAlreadySubscribedError from exc
