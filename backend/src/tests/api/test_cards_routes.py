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
    genres: list[str] | None = None,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
            genres=genres or [],
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
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
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
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма', 'драма', ' фантастика '],
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
        'kinopoisk_id': film.kinopoisk_id,
        'genres': ['комедия'],
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
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['триллер'],
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
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['боевик'],
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
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['фантастика'],
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
    assert body['items'][0]['film_kinopoisk_id'] == film.kinopoisk_id
    assert body['items'][0]['film_genres'] == ['фантастика']
    assert body['items'][0]['rating'] == 9.5
    assert body['items'][0]['custom_tags'] == ['Кинотеатр']


@pytest.mark.asyncio
async def test_create_card_film_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=615)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': 999999,
            'kinopoisk_id': 999999,
            'genres': ['драма'],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_card_by_id_requires_auth(async_client: AsyncClient) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        from models.user import User

        user = User(
            telegram_user_id=777000,
            profile_slug='anon-get-card-test',
            username='anon_tester',
            first_name='Anon',
            last_name='Tester',
            photo_url=None,
            display_name='Anon Tester',
            bio=None,
            language_code='ru',
        )
        film = Film(
            kinopoisk_id=100700,
            title='Оппенгеймер',
            year=2023,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
        )
        session.add(user)
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user.id,
            film_id=film.id,
            rating=9.0,
            company='friends',
            mood_before='thrill',
            mood_after='tense',
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        card_id = card.id

    response = await async_client.get(f'/api/cards/{card_id}')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_card_by_id_success(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=701)
    film = await _create_film(kinopoisk_id=100701, title='Оппенгеймер', year=2023)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['биография', 'драма'],
            'rating': 9.0,
            'company': 'friends',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': ['IMAX'],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    response = await async_client.get(f'/api/cards/{card_id}')
    assert response.status_code == 200
    body = response.json()
    assert body['id'] == card_id
    assert body['film_id'] == film.id
    assert body['film_kinopoisk_id'] == film.kinopoisk_id
    assert body['film_genres'] == ['биография', 'драма']
    assert body['film_title'] == 'Оппенгеймер'
    assert body['film_year'] == 2023
    assert body['film_poster_url'] == 'https://example.com/poster.jpg'
    assert body['rating'] == 9.0
    assert body['custom_tags'] == ['IMAX']


@pytest.mark.asyncio
async def test_get_card_by_id_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=702)
    response = await async_client.get('/api/cards/999999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_card_by_id_accessible_for_another_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=703)
    film = await _create_film(kinopoisk_id=100703, title='Начало', year=2010)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['триллер'],
            'rating': 8.5,
            'company': 'partner',
            'mood_before': 'thrill',
            'mood_after': 'enjoyed',
            'custom_tags': ['Нолан'],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    await _login(async_client, telegram_user_id=704)
    response = await async_client.get(f'/api/cards/{card_id}')
    assert response.status_code == 200
    assert response.json()['film_title'] == 'Начало'


@pytest.mark.asyncio
async def test_create_and_list_comments_flat(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=705)
    film = await _create_film(kinopoisk_id=100705, title='Дюна', year=2021)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['фантастика'],
            'rating': 8.0,
            'company': 'friends',
            'mood_before': 'thrill',
            'mood_after': 'enjoyed',
            'custom_tags': ['IMAX'],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    root = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'Отличный фильм\nСильная режиссура'},
    )
    assert root.status_code == 200
    root_body = root.json()
    assert (
        root_body['parent_comment_id'],
        root_body['author']['id'],
        root_body['text'],
        root_body['total_descendants_count'],
    ) == (None, me['id'], 'Отличный фильм\nСильная режиссура', 0)

    reply = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'Согласен!', 'parent_comment_id': root_body['id']},
    )
    assert reply.status_code == 200
    reply_body = reply.json()
    assert (reply_body['parent_comment_id'], reply_body['total_descendants_count']) == (
        root_body['id'],
        0,
    )

    nested_reply = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'И музыка отличная', 'parent_comment_id': reply_body['id']},
    )
    assert nested_reply.status_code == 200

    logout = await async_client.post('/api/auth/logout')
    assert logout.status_code == 200

    listed = await async_client.get(f'/api/cards/{card_id}/comments')
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body['next_cursor'] is None
    items = listed_body['items']
    assert len(items) == 3

    listed_projection = [
        (
            item['id'],
            item['parent_comment_id'],
            item['replies_count'],
            item['total_descendants_count'],
        )
        for item in items
    ]
    assert listed_projection == [
        (root_body['id'], None, 1, 2),
        (reply_body['id'], root_body['id'], 1, 1),
        (nested_reply.json()['id'], reply_body['id'], 0, 0),
    ]

    replies = await async_client.get(f'/api/cards/{card_id}/comments/{root_body["id"]}/replies')
    assert replies.status_code == 200
    reply_items = replies.json()['items']
    assert len(reply_items) == 1
    assert (reply_items[0]['id'], reply_items[0]['replies_count'], reply_items[0]['total_descendants_count']) == (
        reply_body['id'],
        1,
        1,
    )

    nested = await async_client.get(f'/api/cards/{card_id}/comments/{reply_body["id"]}/replies')
    assert nested.status_code == 200
    nested_items = nested.json()['items']
    assert len(nested_items) == 1
    assert (nested_items[0]['id'], nested_items[0]['total_descendants_count']) == (
        nested_reply.json()['id'],
        0,
    )


@pytest.mark.asyncio
async def test_comments_validation_and_parent_checks(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=706)
    film = await _create_film(kinopoisk_id=100706, title='Бегущий по лезвию 2049', year=2017)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['фантастика'],
            'rating': 9.0,
            'company': 'alone',
            'mood_before': 'thrill',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    too_long = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'x' * 251},
    )
    assert too_long.status_code == 422

    bad_parent = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'reply', 'parent_comment_id': 999999},
    )
    assert bad_parent.status_code == 404

    whitespace_only = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': '   '},
    )
    assert whitespace_only.status_code == 422

    first = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'first'},
    )
    second = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'second'},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    paged = await async_client.get(f'/api/cards/{card_id}/comments?limit=1')
    assert paged.status_code == 200
    paged_body = paged.json()
    assert len(paged_body['items']) == 1
    assert paged_body['next_cursor'] is not None

    paged_next = await async_client.get(
        f'/api/cards/{card_id}/comments?limit=1&cursor={paged_body["next_cursor"]}'
    )
    assert paged_next.status_code == 200
    assert len(paged_next.json()['items']) == 1

    not_found = await async_client.get('/api/cards/999999/comments')
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_comment_create_requires_auth_but_read_is_public(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=707)
    film = await _create_film(kinopoisk_id=100707, title='Солярис', year=1972)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    root = await async_client.post(f'/api/cards/{card_id}/comments', json={'text': 'seed'})
    assert root.status_code == 200
    assert root.json()['author']['id'] == me['id']

    logout = await async_client.post('/api/auth/logout')
    assert logout.status_code == 200

    unauth_create = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'must fail'},
    )
    assert unauth_create.status_code == 401

    public_roots = await async_client.get(f'/api/cards/{card_id}/comments')
    assert public_roots.status_code == 200


@pytest.mark.asyncio
async def test_comment_parent_must_belong_to_same_card(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=708)
    film_one = await _create_film(kinopoisk_id=100708, title='Остров проклятых', year=2010)
    film_two = await _create_film(kinopoisk_id=100709, title='Сияние', year=1980)

    card_one = await async_client.post(
        '/api/cards',
        json={
            'film_id': film_one.id,
            'kinopoisk_id': film_one.kinopoisk_id,
            'genres': ['триллер'],
            'rating': 8.5,
            'company': 'alone',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': [],
        },
    )
    assert card_one.status_code == 200

    card_two = await async_client.post(
        '/api/cards',
        json={
            'film_id': film_two.id,
            'kinopoisk_id': film_two.kinopoisk_id,
            'genres': ['хоррор'],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': [],
        },
    )
    assert card_two.status_code == 200

    root = await async_client.post(
        f'/api/cards/{card_one.json()["id"]}/comments',
        json={'text': 'root on first card'},
    )
    assert root.status_code == 200

    mismatch = await async_client.post(
        f'/api/cards/{card_two.json()["id"]}/comments',
        json={'text': 'wrong parent', 'parent_comment_id': root.json()['id']},
    )
    assert mismatch.status_code == 422


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
            genres=['фантастика', 'боевик'],
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    resolved = await async_client.post(
        '/api/films/resolve',
        json={'url': 'https://www.kinopoisk.ru/film/301/'},
    )
    assert resolved.status_code == 200
    body = resolved.json()
    assert body['kinopoisk_id'] == 301
    assert body['genres'] == ['фантастика', 'боевик']
    assert body['title'] == 'Матрица'

    fetched = await async_client.get(f'/api/films/{body["id"]}')
    assert fetched.status_code == 200
    assert fetched.json()['id'] == body['id']
    assert fetched.json()['genres'] == ['фантастика', 'боевик']

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


@pytest.mark.asyncio
async def test_create_card_kinopoisk_id_mismatch_returns_422(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=618)
    film = await _create_film(kinopoisk_id=12345)
    response = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': 54321,
            'genres': ['драма'],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_card_normalizes_and_persists_film_genres(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=619)
    film = await _create_film(kinopoisk_id=100619, genres=['драма'])
    response = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [' Драма ', 'фантастика', 'драма'],
            'rating': 8.5,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert response.status_code == 200

    details = await async_client.get(f'/api/cards/{response.json()["id"]}')
    assert details.status_code == 200
    assert details.json()['film_genres'] == ['Драма', 'фантастика']
