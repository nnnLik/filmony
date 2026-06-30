from __future__ import annotations

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from models.user_card import UserCard
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


async def _create_planned_card(user_id, *, title: str = 'Inception') -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        from services.cards.create_planned_user_card import CreatePlannedUserCardService

        card = await CreatePlannedUserCardService.build(session).execute(
            user_id,
            'kp:321',
            {
                'provider': 'kinopoisk',
                'data': {
                    'kp_id': 321,
                    'title': title,
                    'poster_url': 'https://example.com/inception.jpg',
                },
            },
        )
        await session.commit()
        await session.refresh(card)
        return card


@pytest.mark.asyncio
async def test_watchlist_feed_post_references_planned_card(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=920000, slug_suffix='actor')
    planned = await _create_planned_card(user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistFeedPostService.build(session)
        post = await service.execute(
            user_id=user.id,
            referenced_user_card_id=int(planned.id),
        )
        await session.commit()

    assert post.user_id == user.id
    assert post.body == ''
    assert post.image_url is None
    assert post.referenced_card_id == planned.id


@pytest.mark.asyncio
async def test_watchlist_feed_post_body_empty_without_snapshot(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=920001, slug_suffix='desc')
    planned = await _create_planned_card(user.id, title='Summer Concert')
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistFeedPostService.build(session)
        post = await service.execute(
            user_id=user.id,
            referenced_user_card_id=int(planned.id),
        )
        await session.commit()

    assert post.body == ''
    assert post.referenced_card_id == planned.id
