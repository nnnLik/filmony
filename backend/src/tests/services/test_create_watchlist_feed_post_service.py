from __future__ import annotations

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from services.feed_posts.create_watchlist_feed_post import CreateWatchlistFeedPostService


async def _create_user(*, telegram_user_id: int, slug_suffix: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'wlfp-{slug_suffix}',
            username=None,
            first_name=None,
            last_name=None,
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_watchlist_feed_post_payload(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=920000, slug_suffix='actor')
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistFeedPostService.build(session)
        post = await service.execute(
            user_id=user.id,
            card_id='kp:321',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 321}},
        )
        await session.commit()

    assert post.user_id == user.id
    assert 'kp:321' in post.body
