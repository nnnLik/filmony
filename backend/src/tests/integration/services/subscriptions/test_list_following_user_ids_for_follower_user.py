"""ListFollowingUserIdsForFollowerUserService — users followed by a subscriber."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from models.user_subscription import UserSubscription
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)


async def _seed_follow_graph() -> tuple[UUID, UUID, UUID]:
    follower = uuid4()
    f1 = uuid4()
    f2 = uuid4()
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                User(
                    id=follower,
                    telegram_user_id=9_510_001,
                    profile_slug=f'flwg{follower.hex[:8]}',
                ),
                User(
                    id=f1,
                    telegram_user_id=9_510_002,
                    profile_slug=f'flwa{f1.hex[:8]}',
                ),
                User(
                    id=f2,
                    telegram_user_id=9_510_003,
                    profile_slug=f'flwb{f2.hex[:8]}',
                ),
            ]
        )
        session.add_all(
            [
                UserSubscription(follower_user_id=follower, following_user_id=f1),
                UserSubscription(follower_user_id=follower, following_user_id=f2),
            ]
        )
        await session.commit()
    return follower, f1, f2


@pytest.mark.asyncio
async def test_lists_following_users_in_stable_order(
    async_client: AsyncClient,
) -> None:
    follower, f1, f2 = await _seed_follow_graph()
    session_factory = get_session_factory()
    async with session_factory() as session:
        out = await ListFollowingUserIdsForFollowerUserService.build(session).execute(follower)
    assert out == tuple(sorted((f1, f2)))
