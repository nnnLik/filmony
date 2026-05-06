from __future__ import annotations

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_film(
    *,
    kinopoisk_id: int = 100500,
    title: str = 'Интерстеллар',
    year: int = 2014,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_create_card_requires_auth(async_client: AsyncClient) -> None:
    film = await _create_film()
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'rating': 7.5,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': ['ночной сеанс'],
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_card_success(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=610)
    film = await _create_film(kinopoisk_id=100501)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'rating': 7.5,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'laughed',
            'custom_tags': ['Пятница', ' IMAX ', 'пятница'],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body['film_id'] == film.id
    assert body['rating'] == 7.5
    assert body['custom_tags'] == ['IMAX', 'Пятница']


@pytest.mark.asyncio
async def test_create_card_duplicate_returns_409(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=611)
    film = await _create_film(kinopoisk_id=100502)
    payload = {
        'film_id': film.id,
        'rating': 8.0,
        'company': 'family',
        'mood_before': 'relax',
        'mood_after': 'enjoyed',
        'custom_tags': [],
    }
    first = await async_client.post('/api/cards', json=payload)
    assert first.status_code == 200
    second = await async_client.post('/api/cards', json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_create_card_validation_0_5_step(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=612)
    film = await _create_film(kinopoisk_id=100503)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'rating': 7.3,
            'company': 'alone',
            'mood_before': 'sad',
            'mood_after': 'cried',
            'custom_tags': [],
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_card_too_many_tags(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=613)
    film = await _create_film(kinopoisk_id=100504)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'rating': 6.5,
            'company': 'partner',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': ['a', 'b', 'c', 'd', 'e', 'f'],
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_profile_cards_and_count_reflect_created_card(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=614)
    film = await _create_film(kinopoisk_id=100505)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'rating': 9.5,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'laughed',
            'custom_tags': ['Кинотеатр'],
        },
    )
    assert created.status_code == 200

    profile = await async_client.get('/api/me/profile')
    assert profile.status_code == 200
    assert profile.json()['cards_count'] == 1

    cards = await async_client.get(f'/api/users/{me["id"]}/cards')
    assert cards.status_code == 200
    body = cards.json()
    assert len(body['items']) == 1
    assert body['items'][0]['film_title'] == 'Интерстеллар'
    assert body['items'][0]['rating'] == 9.5
    assert body['items'][0]['custom_tags'] == ['Кинотеатр']


@pytest.mark.asyncio
async def test_create_card_film_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=615)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': 999999,
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_resolve_film_and_get_by_id(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=616)

    async def fake_get_film(self: object, kinopoisk_id: int):
        from services.kinopoisk.client import KinopoiskFilmPayload

        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title='Матрица',
            year=1999,
            poster_url='https://example.com/matrix.jpg',
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    resolved = await async_client.post(
        '/api/films/resolve',
        json={'url': 'https://www.kinopoisk.ru/film/301/'},
    )
    assert resolved.status_code == 200
    body = resolved.json()
    assert body['kinopoisk_id'] == 301
    assert body['title'] == 'Матрица'

    fetched = await async_client.get(f'/api/films/{body["id"]}')
    assert fetched.status_code == 200
    assert fetched.json()['id'] == body['id']

    # second resolve must be idempotent (same film row)
    resolved_again = await async_client.post(
        '/api/films/resolve',
        json={'url': 'https://www.kinopoisk.ru/film/301/'},
    )
    assert resolved_again.status_code == 200
    assert resolved_again.json()['id'] == body['id']


@pytest.mark.asyncio
async def test_resolve_film_invalid_url(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=617)
    r = await async_client.post('/api/films/resolve', json={'url': 'https://example.com/not-kino'})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_card_model_uses_unique_user_film_pair() -> None:
    # Regression guard to keep 409 behavior stable.
    constraints = {constraint.name for constraint in MovieCard.__table__.constraints}
    assert 'uq_movie_card_user_film' in constraints
