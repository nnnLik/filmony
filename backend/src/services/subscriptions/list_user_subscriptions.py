from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription


class SubscriptionListType(StrEnum):
    followers = 'followers'
    following = 'following'
    both = 'both'


class SubscriptionRelationType(StrEnum):
    follower = 'follower'
    following = 'following'


@dataclass(frozen=True, slots=True)
class SubscriptionListItem:
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    relation_type: SubscriptionRelationType


class TargetUserNotFoundError(Exception):
    pass


class ListUserSubscriptionsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, target_user_id: UUID, relation_filter: SubscriptionListType
    ) -> list[SubscriptionListItem]:
        target = await self._session.execute(select(User.id).where(User.id == target_user_id))
        if target.scalar_one_or_none() is None:
            raise TargetUserNotFoundError

        items: list[SubscriptionListItem] = []
        if relation_filter in (SubscriptionListType.followers, SubscriptionListType.both):
            items.extend(
                await self._fetch_items(
                    self._followers_statement(target_user_id),
                    SubscriptionRelationType.follower,
                )
            )
        if relation_filter in (SubscriptionListType.following, SubscriptionListType.both):
            items.extend(
                await self._fetch_items(
                    self._following_statement(target_user_id),
                    SubscriptionRelationType.following,
                )
            )
        return items

    def _followers_statement(self, target_user_id: UUID) -> Select[tuple[User]]:
        return (
            select(User)
            .join(UserSubscription, User.id == UserSubscription.follower_user_id)
            .where(UserSubscription.following_user_id == target_user_id)
            .order_by(UserSubscription.created_at.desc())
        )

    def _following_statement(self, target_user_id: UUID) -> Select[tuple[User]]:
        return (
            select(User)
            .join(UserSubscription, User.id == UserSubscription.following_user_id)
            .where(UserSubscription.follower_user_id == target_user_id)
            .order_by(UserSubscription.created_at.desc())
        )

    async def _fetch_items(
        self, statement: Select[tuple[User]], relation_type: SubscriptionRelationType
    ) -> list[SubscriptionListItem]:
        result = await self._session.execute(statement)
        users = result.scalars().all()
        return [
            SubscriptionListItem(
                id=user.id,
                profile_slug=user.profile_slug,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                photo_url=user.photo_url,
                display_name=user.display_name,
                relation_type=relation_type,
            )
            for user in users
        ]
