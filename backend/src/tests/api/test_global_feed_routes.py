from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.user import User
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_film(*, kinopoisk_id: int = 900001) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Test Film',
            year=2020,
            poster_url='https://example.com/p.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_global_feed_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/feed/global')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_global_feed_cards_and_posts_chronology(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71001)
    film = await _create_film(kinopoisk_id=71002)
    r_card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r_card.status_code == 200
    card_id = int(r_card.json()['id'])

    r_post = await async_client.post(
        '/api/feed-posts',
        json={'body': 'hello global feed'},
    )
    assert r_post.status_code == 200
    post_id = int(r_post.json()['id'])

    r_all = await async_client.get('/api/feed/global?limit=20&kind=all')
    assert r_all.status_code == 200
    body = r_all.json()
    assert 'feed_head_version' in body
    assert isinstance(body['feed_head_version'], int)
    kinds = [it['kind'] for it in body['items']]
    assert 'movie_card' in kinds and 'feed_post' in kinds
    card_ids_all = [it['id'] for it in body['items'] if it['kind'] == 'movie_card']
    assert card_id in card_ids_all
    # Пост создан позже — первым в хронологии
    assert kinds[0] == 'feed_post'
    assert body['items'][0]['id'] == post_id

    r_posts = await async_client.get('/api/feed/global?kind=posts')
    assert r_posts.status_code == 200
    assert all(it['kind'] == 'feed_post' for it in r_posts.json()['items'])

    r_cards = await async_client.get('/api/feed/global?kind=cards')
    assert r_cards.status_code == 200
    assert all(it['kind'] == 'movie_card' for it in r_cards.json()['items'])
    assert r_cards.json()['items'][0]['id'] == card_id


@pytest.mark.asyncio
async def test_global_feed_movie_card_has_feed_source_global(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71003)
    film = await _create_film(kinopoisk_id=71004)
    await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 7.0,
            'company': 'friends',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    r = await async_client.get('/api/feed/global?kind=cards&limit=5')
    assert r.status_code == 200
    it = r.json()['items'][0]
    assert it['feed_source'] == 'global'


@pytest.mark.asyncio
async def test_global_feed_pagination_cursor(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71005)
    for i in range(3):
        film = await _create_film(kinopoisk_id=71060 + i)
        await async_client.post(
            '/api/cards',
            json={
                'film_id': film.id,
                'kinopoisk_id': film.kinopoisk_id,
                'genres': film.genres,
                'rating': float(5 + i),
                'company': 'alone',
                'mood_before': 'relax',
                'mood_after': 'enjoyed',
                'custom_tags': [f't{i}'],
            },
        )
    first = await async_client.get('/api/feed/global?kind=cards&limit=2')
    assert first.status_code == 200
    c1 = first.json()['next_cursor']
    assert c1
    second = await async_client.get(f'/api/feed/global?kind=cards&limit=2&cursor={c1}')
    assert second.status_code == 200
    ids_page1 = {it['id'] for it in first.json()['items']}
    ids_page2 = {it['id'] for it in second.json()['items']}
    assert ids_page1.isdisjoint(ids_page2)


@pytest.mark.asyncio
async def test_global_feed_head_version_bumps_on_new_card(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71007)
    v0 = (await async_client.get('/api/feed/global?limit=1')).json()['feed_head_version']
    film = await _create_film(kinopoisk_id=71070)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 200
    v1 = (await async_client.get('/api/feed/global?limit=1')).json()['feed_head_version']
    assert v1 > v0


@pytest.mark.asyncio
async def test_global_feed_includes_other_users_cards(async_client: AsyncClient) -> None:
    """Глобальная лента видит карточки другого пользователя."""
    await _login(async_client, telegram_user_id=71008)
    film = await _create_film(kinopoisk_id=71009)
    r_other = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 9.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r_other.status_code == 200
    other_card_id = int(r_other.json()['id'])

    await _login(async_client, telegram_user_id=71010)
    r = await async_client.get('/api/feed/global?kind=cards&limit=50')
    assert r.status_code == 200
    ids = {it['id'] for it in r.json()['items']}
    assert other_card_id in ids

    session_factory = get_session_factory()
    async with session_factory() as session:
        uid = (
            await session.execute(select(User.id).where(User.telegram_user_id == 71008))
        ).scalar_one()
        author_id = str(uid)
    items = r.json()['items']
    match = next(x for x in items if x['id'] == other_card_id)
    assert str(match['user_id']) == author_id


@pytest.mark.asyncio
async def test_global_feed_exclude_own_hides_viewer_posts_and_cards(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=71011)
    viewer_uuid = str(me['id'])
    film = await _create_film(kinopoisk_id=71012)
    r_card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r_card.status_code == 200
    r_post = await async_client.post('/api/feed-posts', json={'body': 'only mine'})
    assert r_post.status_code == 200

    r_all = await async_client.get('/api/feed/global?kind=all&limit=50')
    assert r_all.status_code == 200
    assert any(it['user_id'] == viewer_uuid for it in r_all.json()['items'])

    r_hide = await async_client.get('/api/feed/global?kind=all&limit=50&exclude_own=true')
    assert r_hide.status_code == 200
    assert all(it['user_id'] != viewer_uuid for it in r_hide.json()['items'])

    r_posts_hide = await async_client.get('/api/feed/global?kind=posts&limit=50&exclude_own=true')
    assert r_posts_hide.status_code == 200
    assert all(it['user_id'] != viewer_uuid for it in r_posts_hide.json()['items'])

    r_cards_hide = await async_client.get('/api/feed/global?kind=cards&limit=50&exclude_own=true')
    assert r_cards_hide.status_code == 200
    assert all(it['user_id'] != viewer_uuid for it in r_cards_hide.json()['items'])
