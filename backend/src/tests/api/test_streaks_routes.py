"""Rating streak API routes."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from api.streaks.schemas import STREAK_BATCH_MAX_IDS
from conf import settings
from core.database import get_session_factory
from httpx import AsyncClient
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user_card import UserCard

from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    return response.json()


async def _seed_rated_card_on_day(
    *,
    user_id: UUID,
    kinopoisk_id: int,
    day: date,
    rating: float = 8.0,
    is_planned: bool = False,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=f'Streak Film {kinopoisk_id}',
            year=2024,
            poster_url='https://example.com/streak.jpg',
            genres=[],
        )
        session.add(film)
        await session.flush()
        category_id = await ensure_default_category(session, user_id)
        session.add(
            UserCard(
                user_id=user_id,
                film_id=film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(kinopoisk_id),
                rating=rating,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=is_planned,
                completed_at=datetime.combine(day, datetime.min.time(), tzinfo=UTC),
            )
        )
        await session.commit()


async def _seed_consecutive_streak(
    *,
    user_id: UUID,
    end_day: date,
    length: int,
    kinopoisk_id_base: int,
) -> None:
    for offset in range(length):
        day = end_day - timedelta(days=length - 1 - offset)
        await _seed_rated_card_on_day(
            user_id=user_id,
            kinopoisk_id=kinopoisk_id_base + offset,
            day=day,
        )


@pytest.mark.asyncio
async def test_streak_batch_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.post('/api/streaks/batch', json={'user_ids': []})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_streak_batch_empty_returns_empty_items(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=930001)
    response = await async_client.post('/api/streaks/batch', json={'user_ids': []})
    assert response.status_code == 200
    assert response.json()['items'] == {}


@pytest.mark.asyncio
async def test_streak_batch_rejects_too_many_user_ids(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=930002)
    response = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(uuid4()) for _ in range(STREAK_BATCH_MAX_IDS + 1)]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_streak_zero_omitted_from_batch(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930010)
    user_id = UUID(str(user['id']))
    await _login(async_client, telegram_user_id=930011)

    response = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert response.status_code == 200
    assert response.json()['items'] == {}

    me = await async_client.get('/api/me/streak')
    assert me.status_code == 200
    assert me.json()['current'] == 0


@pytest.mark.asyncio
async def test_streak_three_omitted_from_batch(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930020)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_consecutive_streak(
        user_id=user_id,
        end_day=today,
        length=3,
        kinopoisk_id_base=930_200,
    )

    await _login(async_client, telegram_user_id=930021)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    assert batch.json()['items'] == {}

    await _login(async_client, telegram_user_id=930020)
    me = await async_client.get('/api/me/streak')
    assert me.status_code == 200
    assert me.json()['current'] == 3


@pytest.mark.asyncio
async def test_streak_four_included_in_batch(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930030)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_consecutive_streak(
        user_id=user_id,
        end_day=today,
        length=4,
        kinopoisk_id_base=930_300,
    )

    await _login(async_client, telegram_user_id=930031)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    items = batch.json()['items']
    assert items[str(user_id)] == {'current': 4}


@pytest.mark.asyncio
async def test_streak_ten_included_in_batch(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930040)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_consecutive_streak(
        user_id=user_id,
        end_day=today,
        length=10,
        kinopoisk_id_base=930_400,
    )

    await _login(async_client, telegram_user_id=930041)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    assert batch.json()['items'][str(user_id)] == {'current': 10}


@pytest.mark.asyncio
async def test_streak_fifteen_included_in_batch(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930050)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_consecutive_streak(
        user_id=user_id,
        end_day=today,
        length=15,
        kinopoisk_id_base=930_500,
    )

    await _login(async_client, telegram_user_id=930051)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    assert batch.json()['items'][str(user_id)] == {'current': 15}


@pytest.mark.asyncio
async def test_streak_gap_resets_current_streak(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930060)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_rated_card_on_day(user_id=user_id, kinopoisk_id=930_601, day=today)
    await _seed_rated_card_on_day(
        user_id=user_id,
        kinopoisk_id=930_602,
        day=today - timedelta(days=2),
    )

    await _login(async_client, telegram_user_id=930061)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    assert batch.json()['items'] == {}

    await _login(async_client, telegram_user_id=930060)
    me = await async_client.get('/api/me/streak')
    assert me.status_code == 200
    assert me.json()['current'] == 1


@pytest.mark.asyncio
async def test_streak_excludes_planned_and_low_rating(async_client: AsyncClient) -> None:
    user = await _login(async_client, telegram_user_id=930070)
    user_id = UUID(str(user['id']))
    today = datetime.now(tz=UTC).date()
    await _seed_consecutive_streak(
        user_id=user_id,
        end_day=today - timedelta(days=1),
        length=4,
        kinopoisk_id_base=930_700,
    )
    await _seed_rated_card_on_day(
        user_id=user_id,
        kinopoisk_id=930_750,
        day=today,
        rating=0.0,
        is_planned=False,
    )
    await _seed_rated_card_on_day(
        user_id=user_id,
        kinopoisk_id=930_751,
        day=today,
        rating=8.0,
        is_planned=True,
    )

    await _login(async_client, telegram_user_id=930071)
    batch = await async_client.post(
        '/api/streaks/batch',
        json={'user_ids': [str(user_id)]},
    )
    assert batch.status_code == 200
    assert batch.json()['items'][str(user_id)] == {'current': 4}

    await _login(async_client, telegram_user_id=930070)
    me = await async_client.get('/api/me/streak')
    assert me.status_code == 200
    assert me.json()['current'] == 4
