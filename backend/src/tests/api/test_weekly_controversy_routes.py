"""Weekly controversy API and computation."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from models.weekly_controversy_state import WeeklyControversyState
from services.controversy.compute_weekly_controversy import ComputeWeeklyControversyService
from services.controversy.week_bounds import week_start_for_datetime
from services.telegram.send_weekly_controversy_digest import (
    SendWeeklyControversyTelegramDigestService,
    WeeklyControversyDeliveryOutcome,
)
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    return response.json()


async def _seed_user(
    *,
    telegram_user_id: int | None = None,
    profile_slug: str | None = None,
) -> UUID:
    user_id = uuid4()
    slug = profile_slug or f'wc{user_id.hex[:8]}'
    tid = telegram_user_id if telegram_user_id is not None else int(user_id.int % 9_000_000) + 1_000_000
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            User(
                id=user_id,
                telegram_user_id=tid,
                profile_slug=slug,
                display_name='Controversy User',
            )
        )
        await session.commit()
    return user_id


async def _seed_film(*, kinopoisk_id: int, title: str) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2024,
            poster_url='https://example.com/wc.jpg',
            genres=['drama'],
        )
        session.add(film)
        await session.flush()
        film_id = int(film.id)
        await session.commit()
    return film_id


async def _seed_rated_card(
    *,
    user_id: UUID,
    film_id: int,
    rating: float,
    completed_at: dt.datetime,
    kinopoisk_id: int,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        category_id = await ensure_default_category(session, user_id)
        session.add(
            UserCard(
                user_id=user_id,
                film_id=film_id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(kinopoisk_id),
                rating=rating,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
                completed_at=completed_at,
            )
        )
        await session.commit()


async def _seed_follow(*, follower_id: UUID, following_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            UserSubscription(follower_user_id=follower_id, following_user_id=following_id)
        )
        await session.commit()


@pytest.mark.asyncio
async def test_weekly_controversy_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get('/api/me/weekly-controversy')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_weekly_controversy_empty_without_following(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940001)
    response = await async_client.get('/api/me/weekly-controversy')
    assert response.status_code == 200
    body = response.json()
    assert body['controversy'] is None
    assert 'week_start' in body


@pytest.mark.asyncio
async def test_weekly_controversy_picks_highest_spread(async_client: AsyncClient) -> None:
    viewer_tid = 940002
    await _login(async_client, telegram_user_id=viewer_tid)
    session_factory = get_session_factory()
    async with session_factory() as session:
        viewer = (
            await session.execute(select(User).where(User.telegram_user_id == viewer_tid))
        ).scalar_one()

    author_a = await _seed_user(profile_slug='wca1')
    author_b = await _seed_user(profile_slug='wca2')
    author_c = await _seed_user(profile_slug='wca3')
    await _seed_follow(follower_id=viewer.id, following_id=author_a)
    await _seed_follow(follower_id=viewer.id, following_id=author_b)
    await _seed_follow(follower_id=viewer.id, following_id=author_c)

    now = dt.datetime.now(tz=dt.UTC)
    film_low_spread = await _seed_film(kinopoisk_id=940201, title='Calm Film')
    film_high_spread = await _seed_film(kinopoisk_id=940202, title='Spicy Film')

    for idx, (author, rating) in enumerate(
        [(author_a, 8.0), (author_b, 8.5), (author_c, 9.0)],
        start=1,
    ):
        await _seed_rated_card(
            user_id=author,
            film_id=film_low_spread,
            rating=rating,
            completed_at=now - dt.timedelta(days=idx),
            kinopoisk_id=940201,
        )

    for idx, (author, rating) in enumerate(
        [(author_a, 2.0), (author_b, 7.0), (author_c, 10.0)],
        start=1,
    ):
        await _seed_rated_card(
            user_id=author,
            film_id=film_high_spread,
            rating=rating,
            completed_at=now - dt.timedelta(days=idx),
            kinopoisk_id=940202,
        )

    response = await async_client.get('/api/me/weekly-controversy')
    assert response.status_code == 200
    controversy = response.json()['controversy']
    assert controversy is not None
    assert controversy['title'] == 'Spicy Film'
    assert controversy['spread'] == 8.0
    assert controversy['rater_count'] == 3
    assert controversy['min_rating'] == 2.0
    assert controversy['max_rating'] == 10.0
    assert controversy['anchor_film_id'] == film_high_spread


@pytest.mark.asyncio
async def test_compute_prefers_recent_window_over_all_time_fallback(prepare_db: None) -> None:
    viewer = await _seed_user()
    author_a = await _seed_user(profile_slug='wcf1')
    author_b = await _seed_user(profile_slug='wcf2')
    author_c = await _seed_user(profile_slug='wcf3')
    await _seed_follow(follower_id=viewer, following_id=author_a)
    await _seed_follow(follower_id=viewer, following_id=author_b)
    await _seed_follow(follower_id=viewer, following_id=author_c)

    now = dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.UTC)
    film_id = await _seed_film(kinopoisk_id=940301, title='Fallback Film')

    old = now - dt.timedelta(days=30)
    await _seed_rated_card(
        user_id=author_a,
        film_id=film_id,
        rating=1.0,
        completed_at=old,
        kinopoisk_id=940301,
    )
    await _seed_rated_card(
        user_id=author_b,
        film_id=film_id,
        rating=10.0,
        completed_at=old,
        kinopoisk_id=940301,
    )
    await _seed_rated_card(
        user_id=author_c,
        film_id=film_id,
        rating=5.0,
        completed_at=now - dt.timedelta(days=2),
        kinopoisk_id=940301,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await ComputeWeeklyControversyService.build(session).execute(
            viewer_user_id=viewer,
            now=now,
        )

    assert result is not None
    assert result.spread == 9.0
    assert result.rater_count == 3
    assert result.link_card_id is not None


@pytest.mark.asyncio
async def test_compute_requires_three_distinct_raters(prepare_db: None) -> None:
    viewer = await _seed_user()
    author_a = await _seed_user(profile_slug='wct1')
    author_b = await _seed_user(profile_slug='wct2')
    await _seed_follow(follower_id=viewer, following_id=author_a)
    await _seed_follow(follower_id=viewer, following_id=author_b)

    now = dt.datetime.now(tz=dt.UTC)
    film_id = await _seed_film(kinopoisk_id=940401, title='Two Raters')
    await _seed_rated_card(
        user_id=author_a,
        film_id=film_id,
        rating=2.0,
        completed_at=now - dt.timedelta(days=1),
        kinopoisk_id=940401,
    )
    await _seed_rated_card(
        user_id=author_b,
        film_id=film_id,
        rating=9.0,
        completed_at=now - dt.timedelta(days=1),
        kinopoisk_id=940401,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await ComputeWeeklyControversyService.build(session).execute(
            viewer_user_id=viewer,
            now=now,
        )
    assert result is None


@pytest.mark.asyncio
async def test_digest_is_idempotent_per_week(prepare_db: None) -> None:
    recipient = await _seed_user(telegram_user_id=940501, profile_slug='wcd1')
    author_a = await _seed_user(profile_slug='wcd2')
    author_b = await _seed_user(profile_slug='wcd3')
    author_c = await _seed_user(profile_slug='wcd4')
    await _seed_follow(follower_id=recipient, following_id=author_a)
    await _seed_follow(follower_id=recipient, following_id=author_b)
    await _seed_follow(follower_id=recipient, following_id=author_c)

    now = dt.datetime(2026, 7, 28, 10, 0, tzinfo=dt.UTC)
    film_id = await _seed_film(kinopoisk_id=940501, title='Digest Film')
    for author, rating in [(author_a, 3.0), (author_b, 6.0), (author_c, 9.0)]:
        await _seed_rated_card(
            user_id=author,
            film_id=film_id,
            rating=rating,
            completed_at=now - dt.timedelta(days=1),
            kinopoisk_id=940501,
        )

    session_factory = get_session_factory()
    with patch(
        'services.telegram.send_weekly_controversy_digest.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as deliver_mock:
        async with session_factory() as session:
            first = await SendWeeklyControversyTelegramDigestService.build(session).execute(
                recipient_user_id=recipient,
                now=now,
            )
        assert first.outcome == WeeklyControversyDeliveryOutcome.sent
        deliver_mock.assert_awaited_once()
        html_body = deliver_mock.await_args.args[1]
        assert '⚡' in html_body
        assert 'startapp=c' in html_body
        assert 'Посмотреть мнения подписок' in html_body

        async with session_factory() as session:
            second = await SendWeeklyControversyTelegramDigestService.build(session).execute(
                recipient_user_id=recipient,
                now=now,
            )
        assert second.outcome == WeeklyControversyDeliveryOutcome.skipped_already_sent
        deliver_mock.assert_awaited_once()

    async with session_factory() as session:
        row = (
            await session.execute(
                select(WeeklyControversyState).where(
                    WeeklyControversyState.user_id == recipient,
                    WeeklyControversyState.week_start == week_start_for_datetime(now),
                )
            )
        ).scalar_one()
        assert row.sent_at is not None
        assert row.title == 'Digest Film'
        assert row.spread == 6.0


@pytest.mark.asyncio
async def test_get_returns_persisted_state(async_client: AsyncClient) -> None:
    viewer_tid = 940601
    await _login(async_client, telegram_user_id=viewer_tid)
    session_factory = get_session_factory()
    film_id = await _seed_film(kinopoisk_id=940601, title='Stored Title')
    async with session_factory() as session:
        viewer = (
            await session.execute(select(User).where(User.telegram_user_id == viewer_tid))
        ).scalar_one()
        week_start = week_start_for_datetime(dt.datetime.now(tz=dt.UTC))
        session.add(
            WeeklyControversyState(
                user_id=viewer.id,
                week_start=week_start,
                anchor_film_id=film_id,
                title='Stored Title',
                spread=4.5,
                rater_count=5,
                min_rating=3.0,
                max_rating=7.5,
                sent_at=dt.datetime.now(tz=dt.UTC),
            )
        )
        await session.commit()

    response = await async_client.get('/api/me/weekly-controversy')
    assert response.status_code == 200
    controversy = response.json()['controversy']
    assert controversy is not None
    assert controversy['title'] == 'Stored Title'
    assert controversy['spread'] == 4.5
