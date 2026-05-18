"""ListFollowerUserIdsForFollowingUserService — followers of a publisher with optional exclusion."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from models.user_subscription import UserSubscription
from services.subscriptions.list_follower_user_ids_for_following_user import (
    ListFollowerUserIdsForFollowingUserService,
)


async def _seed_three_users() -> tuple[UUID, UUID, UUID]:
    author = uuid4()
    f1 = uuid4()
    f2 = uuid4()
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                User(
                    id=author,
                    telegram_user_id=9_500_001,
                    profile_slug=f'flwauth{author.hex[:8]}',
                ),
                User(
                    id=f1,
                    telegram_user_id=9_500_002,
                    profile_slug=f'flwf1{f1.hex[:8]}',
                ),
                User(
                    id=f2,
                    telegram_user_id=9_500_003,
                    profile_slug=f'flwf2{f2.hex[:8]}',
                ),
            ]
        )
        session.add_all(
            [
                UserSubscription(follower_user_id=f1, following_user_id=author),
                UserSubscription(follower_user_id=f2, following_user_id=author),
            ]
        )
        await session.commit()
    return author, f1, f2


@pytest.mark.asyncio
async def test_lists_distinct_followers_in_stable_order(
    async_client: AsyncClient,
) -> None:
    author, f1, f2 = await _seed_three_users()
    session_factory = get_session_factory()
    async with session_factory() as session:
        out = await ListFollowerUserIdsForFollowingUserService.build(session).execute(author)
    assert out == (f1, f2)


@pytest.mark.asyncio
async def test_exclude_user_ids_filters_followers(
    async_client: AsyncClient,
) -> None:
    author, f1, f2 = await _seed_three_users()
    session_factory = get_session_factory()
    async with session_factory() as session:
        out = await ListFollowerUserIdsForFollowingUserService.build(session).execute(
            author,
            exclude_user_ids=frozenset({f1}),
        )
    assert out == (f2,)
