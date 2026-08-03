"""Gamification API routes: passport, marathons, shelf physics, contrarian."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.catalog.community_stats_dto import is_contrarian
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    return response.json()


async def _user_id_for_telegram(telegram_user_id: int) -> UUID:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_id = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one()
        return UUID(str(user_id))


async def _create_film(
    *,
    kinopoisk_id: int,
    title: str = 'Test Film',
    year: int | None = 2010,
    countries: list[str] | None = None,
    genres: list[str] | None = None,
    primary_director_kinopoisk_id: int | None = None,
    primary_director_name: str | None = None,
    franchise_key: str | None = None,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
            genres=genres if genres is not None else ['drama'],
            countries=countries or [],
            primary_director_kinopoisk_id=primary_director_kinopoisk_id,
            primary_director_name=primary_director_name,
            franchise_key=franchise_key,
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _catalog_item_for_film(film: Film) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        existing = (
            await session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == film.id),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return int(existing)
        item = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return int(item.id)


async def _seed_rated_card(
    *,
    user_id: UUID,
    film: Film,
    rating: float,
    completed_at: datetime | None = None,
    catalog_item_id: int | None = None,
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        category_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            catalog_item_id=catalog_item_id,
            category_id=category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            completed_at=completed_at or datetime.now(tz=UTC),
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return int(card.id)


@pytest.mark.asyncio
async def test_gamification_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_passport_unlocks_country_and_decade_stamps(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940001)
    user_id = await _user_id_for_telegram(940001)
    film = await _create_film(
        kinopoisk_id=9400011,
        title='Amélie',
        year=2001,
        countries=['France'],
    )
    await _seed_rated_card(user_id=user_id, film=film, rating=8.0)

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    payload = response.json()
    stamp_ids = {stamp['stamp_id'] for stamp in payload['passport']['stamps']}
    assert 'country_first_france' in stamp_ids
    assert 'decade_first_2000' in stamp_ids
    assert payload['passport']['unlocked_count'] >= 2


@pytest.mark.asyncio
async def test_public_passport_returns_only_unlocked(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=940010)
    owner_id = UUID(str(owner['id']))
    film = await _create_film(
        kinopoisk_id=9400101,
        title='Tokyo Story',
        year=1953,
        countries=['Japan'],
    )
    await _seed_rated_card(user_id=owner_id, film=film, rating=9.0)

    await _login(async_client, telegram_user_id=940011)
    response = await async_client.get(f'/api/users/{owner_id}/gamification/passport')
    assert response.status_code == 200
    payload = response.json()
    assert payload['unlocked_count'] == len(payload['stamps'])
    assert all(stamp['unlocked'] for stamp in payload['stamps'])


@pytest.mark.asyncio
async def test_marathon_unlocks_after_five_director_ratings(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940020)
    user_id = await _user_id_for_telegram(940020)
    base_day = datetime(2024, 1, 1, tzinfo=UTC)
    for index in range(5):
        film = await _create_film(
            kinopoisk_id=9400200 + index,
            title=f'Nolan Film {index}',
            year=2010 + index,
            primary_director_kinopoisk_id=525,
            primary_director_name='Christopher Nolan',
        )
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=8.0,
            completed_at=base_day + timedelta(days=index),
        )

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    marathons = response.json()['marathons']
    assert len(marathons) == 1
    assert marathons[0]['kind'] == 'director'
    assert marathons[0]['count'] == 5
    assert marathons[0]['label'] == 'Christopher Nolan'


@pytest.mark.asyncio
async def test_marathon_franchise_unlock(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940030)
    user_id = await _user_id_for_telegram(940030)
    franchise = 'kp_franchise:301'
    for index in range(5):
        film = await _create_film(
            kinopoisk_id=9400300 + index,
            title=f'Matrix Part {index}',
            year=1999 + index,
            franchise_key=franchise,
        )
        await _seed_rated_card(user_id=user_id, film=film, rating=7.5)

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    marathons = response.json()['marathons']
    assert any(item['kind'] == 'franchise' and item['count'] == 5 for item in marathons)


@pytest.mark.asyncio
async def test_shelf_physics_slump_on_three_low_ratings(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940040)
    user_id = await _user_id_for_telegram(940040)
    base_day = datetime(2025, 6, 1, tzinfo=UTC)
    ratings = [2.0, 1.5, 3.0, 8.0, 9.0]
    for index, rating in enumerate(ratings):
        film = await _create_film(kinopoisk_id=9400400 + index, title=f'Film {index}')
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=rating,
            completed_at=base_day + timedelta(days=len(ratings) - index),
        )

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    shelf = response.json()['shelf_physics']
    assert shelf['mode'] == 'slump'
    assert shelf['streak_length'] == 3


@pytest.mark.asyncio
async def test_shelf_physics_glow_on_three_high_ratings(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940050)
    user_id = await _user_id_for_telegram(940050)
    base_day = datetime(2025, 7, 1, tzinfo=UTC)
    ratings = [9.5, 10.0, 9.0, 4.0]
    for index, rating in enumerate(ratings):
        film = await _create_film(kinopoisk_id=9400500 + index, title=f'Great {index}')
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=rating,
            completed_at=base_day + timedelta(days=len(ratings) - index),
        )

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    shelf = response.json()['shelf_physics']
    assert shelf['mode'] == 'glow'
    assert shelf['streak_length'] == 3


@pytest.mark.asyncio
async def test_is_contrarian_boundary_helper() -> None:
    assert is_contrarian(user_rating=10.0, avg_rating=6.0, ratings_count=3) is True
    assert is_contrarian(user_rating=10.0, avg_rating=6.1, ratings_count=3) is False
    assert is_contrarian(user_rating=10.0, avg_rating=6.0, ratings_count=2) is False


async def _ensure_user(telegram_user_id: int) -> UUID:
    session_factory = get_session_factory()
    async with session_factory() as session:
        existing = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return UUID(str(existing))
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'u{telegram_user_id}'[:32],
            username=f'user{telegram_user_id}',
            first_name='Test',
            last_name='User',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return UUID(str(user.id))


async def _seed_community_ratings(
    *,
    film: Film,
    catalog_id: int,
    ratings: list[tuple[int, float]],
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        for telegram_user_id, rating in ratings:
            user_id = await _ensure_user(telegram_user_id)
            category_id = await ensure_default_category(session, user_id)
            session.add(
                UserCard(
                    user_id=user_id,
                    film_id=film.id,
                    catalog_item_id=catalog_id,
                    category_id=category_id,
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(film.kinopoisk_id),
                    rating=rating,
                    company='alone',
                    mood_before='relax',
                    mood_after='enjoyed',
                    completed_at=datetime.now(tz=UTC),
                )
            )
        await session.commit()


@pytest.mark.asyncio
async def test_card_detail_contrarian_when_delta_at_least_four(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=940060)
    owner_id = UUID(str(owner['id']))

    film = await _create_film(kinopoisk_id=9400601, title='Community Film')
    catalog_id = await _catalog_item_for_film(film)
    await _seed_community_ratings(
        film=film,
        catalog_id=catalog_id,
        ratings=[(940061, 4.0), (940062, 4.0), (940063, 4.0)],
    )

    owner_card_id = await _seed_rated_card(
        user_id=owner_id,
        film=film,
        rating=10.0,
        catalog_item_id=catalog_id,
    )

    await _login(async_client, telegram_user_id=940060)
    detail = await async_client.get(f'/api/cards/{owner_card_id}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['community_avg_rating'] == 5.5
    assert body['is_contrarian'] is True


@pytest.mark.asyncio
async def test_card_detail_not_contrarian_when_delta_below_four(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=940070)
    owner_id = UUID(str(owner['id']))

    film = await _create_film(kinopoisk_id=9400701, title='Almost Contrarian')
    catalog_id = await _catalog_item_for_film(film)
    await _seed_community_ratings(
        film=film,
        catalog_id=catalog_id,
        ratings=[(940071, 6.6), (940072, 6.6), (940073, 6.6)],
    )

    owner_card_id = await _seed_rated_card(
        user_id=owner_id,
        film=film,
        rating=10.0,
        catalog_item_id=catalog_id,
    )

    await _login(async_client, telegram_user_id=940070)
    detail = await async_client.get(f'/api/cards/{owner_card_id}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['community_avg_rating'] == 7.4
    assert body['is_contrarian'] is False


@pytest.mark.asyncio
async def test_contrarian_hidden_for_non_owner_viewer(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=940080)
    owner_id = UUID(str(owner['id']))
    film = await _create_film(kinopoisk_id=9400801, title='Hidden Badge')
    catalog_id = await _catalog_item_for_film(film)
    await _seed_community_ratings(
        film=film,
        catalog_id=catalog_id,
        ratings=[(940081, 5.0), (940082, 5.0), (940083, 5.0)],
    )

    owner_card_id = await _seed_rated_card(
        user_id=owner_id,
        film=film,
        rating=10.0,
        catalog_item_id=catalog_id,
    )

    await _login(async_client, telegram_user_id=940084)
    detail = await async_client.get(f'/api/cards/{owner_card_id}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['community_avg_rating'] == 6.2
    assert body['is_contrarian'] is False


@pytest.mark.asyncio
async def test_rated_directors_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get(f'/api/users/{uuid4()}/rated-directors')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rated_directors_lists_directors_with_counts(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940100)
    user_id = await _user_id_for_telegram(940100)
    nolan = 525
    for index in range(3):
        film = await _create_film(
            kinopoisk_id=9401000 + index,
            title=f'Nolan Film {index}',
            primary_director_kinopoisk_id=nolan,
            primary_director_name='Christopher Nolan',
        )
        await _seed_rated_card(user_id=user_id, film=film, rating=8.0)
    other = await _create_film(
        kinopoisk_id=9401009,
        title='Other Director Film',
        primary_director_kinopoisk_id=999,
        primary_director_name='Other Director',
    )
    await _seed_rated_card(user_id=user_id, film=other, rating=7.0)

    await _login(async_client, telegram_user_id=940100)
    response = await async_client.get(f'/api/users/{user_id}/rated-directors')
    assert response.status_code == 200
    items = response.json()['items']
    assert len(items) == 2
    assert items[0]['kinopoisk_id'] == nolan
    assert items[0]['name'] == 'Christopher Nolan'
    assert items[0]['count'] == 3


@pytest.mark.asyncio
async def test_list_user_cards_filter_by_director(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=940110)
    user_id = UUID(str(me['id']))
    nolan_id = 525
    nolan_film = await _create_film(
        kinopoisk_id=9401101,
        title='Inception',
        primary_director_kinopoisk_id=nolan_id,
        primary_director_name='Christopher Nolan',
    )
    other_film = await _create_film(
        kinopoisk_id=9401102,
        title='Other Film',
        primary_director_kinopoisk_id=999,
    )
    await _seed_rated_card(user_id=user_id, film=nolan_film, rating=9.0)
    await _seed_rated_card(user_id=user_id, film=other_film, rating=8.0)

    response = await async_client.get(
        f'/api/users/{user_id}/cards',
        params={'director_kinopoisk_id': nolan_id},
    )
    assert response.status_code == 200
    items = response.json()['items']
    assert len(items) == 1
    assert items[0]['film_title'] == 'Inception'


@pytest.mark.asyncio
async def test_list_user_cards_filter_by_franchise(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=940120)
    user_id = UUID(str(me['id']))
    franchise = 'kp_franchise:301'
    matrix_film = await _create_film(
        kinopoisk_id=9401201,
        title='Matrix',
        franchise_key=franchise,
    )
    other_film = await _create_film(
        kinopoisk_id=9401202,
        title='Standalone',
        franchise_key='kp_franchise:999',
    )
    await _seed_rated_card(user_id=user_id, film=matrix_film, rating=9.0)
    await _seed_rated_card(user_id=user_id, film=other_film, rating=8.0)

    response = await async_client.get(
        f'/api/users/{user_id}/cards',
        params={'franchise_key': franchise},
    )
    assert response.status_code == 200
    items = response.json()['items']
    assert len(items) == 1
    assert items[0]['film_title'] == 'Matrix'


@pytest.mark.asyncio
async def test_passport_director_first_and_fan_stamps(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940130)
    user_id = await _user_id_for_telegram(940130)
    director_id = 777
    for index in range(3):
        film = await _create_film(
            kinopoisk_id=9401300 + index,
            title=f'Director Film {index}',
            primary_director_kinopoisk_id=director_id,
            primary_director_name='Test Director',
        )
        await _seed_rated_card(user_id=user_id, film=film, rating=8.0)

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    stamp_ids = {stamp['stamp_id'] for stamp in response.json()['passport']['stamps']}
    assert f'director_first_{director_id}' in stamp_ids
    assert f'director_fan_{director_id}' in stamp_ids


@pytest.mark.asyncio
async def test_passport_genres_total_and_first_rating_stamps(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940140)
    user_id = await _user_id_for_telegram(940140)
    genres = ['drama', 'comedy', 'thriller', 'sci-fi', 'romance']
    for index, genre in enumerate(genres):
        film = await _create_film(
            kinopoisk_id=9401400 + index,
            title=f'Genre Film {index}',
            genres=[genre],
        )
        rating = 10.0 if index == 0 else 8.0
        await _seed_rated_card(user_id=user_id, film=film, rating=rating)

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    stamps = {stamp['stamp_id']: stamp for stamp in response.json()['passport']['stamps']}
    assert stamps['genres_total_5']['unlocked'] is True
    assert stamps['first_rating_10']['unlocked'] is True


@pytest.mark.asyncio
async def test_passport_binge_day_and_high_streak_stamps(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940150)
    user_id = await _user_id_for_telegram(940150)
    binge_day = datetime(2025, 3, 15, 12, 0, tzinfo=UTC)
    for index in range(3):
        film = await _create_film(kinopoisk_id=9401500 + index, title=f'Binge {index}')
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=9.5,
            completed_at=binge_day + timedelta(hours=index),
        )
    for index in range(3, 6):
        film = await _create_film(kinopoisk_id=9401500 + index, title=f'Streak {index}')
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=9.0,
            completed_at=binge_day + timedelta(days=index),
        )

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    stamps = {stamp['stamp_id']: stamp for stamp in response.json()['passport']['stamps']}
    assert stamps['binge_day']['unlocked'] is True
    assert stamps['binge_day']['progress_current'] == 3
    assert stamps['high_streak_3']['unlocked'] is True


@pytest.mark.asyncio
async def test_passport_chrono_year_horror_mood_swings(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=940160)
    user_id = await _user_id_for_telegram(940160)
    base = datetime(2024, 6, 1, tzinfo=UTC)
    years = [1965, 1975, 1985]
    for index, year in enumerate(years):
        film = await _create_film(
            kinopoisk_id=9401600 + index,
            title=f'Chrono {year}',
            year=year,
        )
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=8.0,
            completed_at=base + timedelta(days=index),
        )
    for index in range(5):
        film = await _create_film(
            kinopoisk_id=9401610 + index,
            title=f'Horror {index}',
            genres=['Ужасы'],
        )
        await _seed_rated_card(
            user_id=user_id,
            film=film,
            rating=6.0,
            completed_at=base + timedelta(days=10 + index),
        )
    low_film = await _create_film(kinopoisk_id=9401620, title='Low Mood')
    high_film = await _create_film(kinopoisk_id=9401621, title='High Mood')
    await _seed_rated_card(
        user_id=user_id,
        film=low_film,
        rating=2.0,
        completed_at=base + timedelta(days=20),
    )
    await _seed_rated_card(
        user_id=user_id,
        film=high_film,
        rating=10.0,
        completed_at=base + timedelta(days=22),
    )

    response = await async_client.get('/api/me/gamification')
    assert response.status_code == 200
    stamps = {stamp['stamp_id']: stamp for stamp in response.json()['passport']['stamps']}
    assert stamps['chrono_year_2024']['unlocked'] is True
    assert stamps['horror_survivor']['unlocked'] is True
    assert stamps['mood_swings']['unlocked'] is True
    assert stamps['first_rating_1']['unlocked'] is False
