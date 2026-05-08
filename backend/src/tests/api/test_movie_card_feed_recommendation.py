from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag
from models.user_subscription import UserSubscription
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _seed_movie_card_for_user(
    *,
    user_id: UUID,
    kinopoisk_id: int,
    genres: list[str],
    tags: list[str] | None = None,
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=f'Film {kinopoisk_id}',
            year=2020,
            poster_url='https://example.com/p.jpg',
            genres=genres,
        )
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user_id,
            film_id=film.id,
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        for t in tags or []:
            session.add(MovieCardTag(movie_card_id=card.id, tag=t))
        await session.commit()
        await session.refresh(card)
        return card.id


async def _subscribe(follower_id: UUID, following_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=follower_id, following_user_id=following_id))
        await session.commit()


@pytest.mark.asyncio
async def test_feed_happy_path_shows_followed_author_cards(async_client: AsyncClient) -> None:
    viewer = await _login(async_client, telegram_user_id=9601)
    author = await _login(async_client, telegram_user_id=9602)
    v_id = UUID(str(viewer['id']))
    a_id = UUID(str(author['id']))
    await _subscribe(v_id, a_id)

    await _login(async_client, telegram_user_id=9601)
    cid = await _seed_movie_card_for_user(
        user_id=a_id, kinopoisk_id=1960101, genres=['драма'], tags=['ночь']
    )

    feed = await async_client.get('/api/cards/feed?limit=20')
    assert feed.status_code == 200
    body = feed.json()
    ours = next((it for it in body['items'] if it['id'] == cid), None)
    assert ours is not None
    assert ours['user_id'] == str(a_id)
    assert ours['feed_source'] == 'subscriptions'


@pytest.mark.asyncio
async def test_feed_empty_social_graph_fills_from_discovery(async_client: AsyncClient) -> None:
    viewer = await _login(async_client, telegram_user_id=9603)
    stranger = await _login(async_client, telegram_user_id=9604)
    v_id = UUID(str(viewer['id']))
    s_id = UUID(str(stranger['id']))

    await _seed_movie_card_for_user(user_id=s_id, kinopoisk_id=1960301, genres=['комедия'])
    await _seed_movie_card_for_user(user_id=s_id, kinopoisk_id=1960302, genres=['триллер'])

    await _login(async_client, telegram_user_id=9603)
    feed = await async_client.get('/api/cards/feed?limit=10')
    assert feed.status_code == 200
    body = feed.json()
    for it in body['items']:
        assert it['feed_source'] in (
            'own',
            'subscriptions',
            'subscribers',
            'personal_affinity',
            'discovery',
        )
    ids_on_page = [it['user_id'] for it in body['items']]
    assert str(s_id) in ids_on_page
    assert str(v_id) not in ids_on_page


@pytest.mark.asyncio
async def test_feed_cursor_same_response_on_repeat(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=9605)
    from tests.api.test_cards_routes import _create_film

    for kid in (1960501, 1960502, 1960503):
        film = await _create_film(kinopoisk_id=kid, genres=[])
        r = await async_client.post(
            '/api/cards',
            json={
                'film_id': film.id,
                'kinopoisk_id': film.kinopoisk_id,
                'genres': [],
                'rating': 7.0,
                'company': 'alone',
                'mood_before': 'relax',
                'mood_after': 'enjoyed',
                'custom_tags': [],
            },
        )
        assert r.status_code == 200

    first = await async_client.get('/api/cards/feed?limit=2')
    assert first.status_code == 200
    c = first.json().get('next_cursor')
    assert c is not None

    a = await async_client.get(f'/api/cards/feed?limit=2&cursor={c}')
    b = await async_client.get(f'/api/cards/feed?limit=2&cursor={c}')
    assert a.status_code == 200 and b.status_code == 200
    assert [x['id'] for x in a.json()['items']] == [x['id'] for x in b.json()['items']]


@pytest.mark.asyncio
async def test_feed_dedup_unique_ids(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=9606)
    from tests.api.test_cards_routes import _create_film

    for kid in range(1960600, 1960610):
        film = await _create_film(kinopoisk_id=kid, genres=[])
        r = await async_client.post(
            '/api/cards',
            json={
                'film_id': film.id,
                'kinopoisk_id': film.kinopoisk_id,
                'genres': [],
                'rating': 7.0,
                'company': 'alone',
                'mood_before': 'relax',
                'mood_after': 'enjoyed',
                'custom_tags': [],
            },
        )
        assert r.status_code == 200
    feed = await async_client.get('/api/cards/feed?limit=50')
    ids = [it['id'] for it in feed.json()['items']]
    assert len(ids) == len(set(ids))


@pytest.mark.asyncio
async def test_feed_discovery_appears_with_social_graph(async_client: AsyncClient) -> None:
    viewer = await _login(async_client, telegram_user_id=9610)
    followed = await _login(async_client, telegram_user_id=9611)
    stranger = await _login(async_client, telegram_user_id=9612)
    v_id = UUID(str(viewer['id']))
    f_id = UUID(str(followed['id']))
    s_id = UUID(str(stranger['id']))
    await _subscribe(v_id, f_id)

    for offset in range(5):
        await _seed_movie_card_for_user(
            user_id=f_id, kinopoisk_id=1_961_100 + offset, genres=['драма']
        )
    for offset in range(10):
        await _seed_movie_card_for_user(
            user_id=s_id, kinopoisk_id=1_961_300 + offset, genres=['фантастика']
        )

    await _login(async_client, telegram_user_id=9610)
    feed = await async_client.get('/api/cards/feed?limit=40')
    assert feed.status_code == 200
    items = feed.json()['items']
    stranger_hits = sum(1 for it in items if it['user_id'] == str(s_id))
    assert stranger_hits >= 1
    for it in items:
        if it['user_id'] == str(s_id):
            assert it['feed_source'] in ('discovery', 'personal_affinity')


@pytest.mark.asyncio
async def test_feed_subscriptions_only_excludes_non_subscription_streams(
    async_client: AsyncClient,
) -> None:
    me = await _login(async_client, telegram_user_id=9620)
    followed = await _login(async_client, telegram_user_id=9621)
    stranger = await _login(async_client, telegram_user_id=9622)
    v_id = UUID(str(me['id']))
    f_id = UUID(str(followed['id']))
    s_id = UUID(str(stranger['id']))
    await _subscribe(v_id, f_id)

    await _seed_movie_card_for_user(user_id=f_id, kinopoisk_id=1962001, genres=['драма'])
    await _seed_movie_card_for_user(user_id=s_id, kinopoisk_id=1962002, genres=['комедия'])

    await _login(async_client, telegram_user_id=9620)
    mix = await async_client.get('/api/cards/feed?limit=50')
    assert mix.status_code == 200
    mix_items = mix.json()['items']
    assert any(it['user_id'] == str(s_id) for it in mix_items)

    sub_only = await async_client.get('/api/cards/feed?limit=50&mode=subscriptions_only')
    assert sub_only.status_code == 200
    sub_items = sub_only.json()['items']
    assert str(s_id) not in [it['user_id'] for it in sub_items]
    assert all(it['feed_source'] in ('own', 'subscriptions') for it in sub_items)
