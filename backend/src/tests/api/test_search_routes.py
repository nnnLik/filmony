from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.user import User
from models.user_subscription import UserSubscription
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_search_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/search', params={'q': 'ab'})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_suggestions_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_search_rejects_short_query_after_trim(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=7101)
    r = await async_client.get('/api/search', params={'q': '  a  '})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_search_returns_films_and_users(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=7102)
    uid = UUID(str(data['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Film(
                kinopoisk_id=910_001,
                title='УникальныйТайтлПоиска',
                year=2020,
                poster_url=None,
                genres=[],
            )
        )
        res = await session.execute(select(User).where(User.id == uid))
        me = res.scalar_one()
        me.display_name = 'УникальноеИмяПоиска'
        session.add(me)
        await session.commit()

    r = await async_client.get('/api/search', params={'q': 'Уникальн'})
    assert r.status_code == 200
    body = r.json()
    assert any('Уникальный' in f['title'] for f in body['films'])
    assert any(body['users'][i]['id'] == str(uid) for i in range(len(body['users'])))


@pytest.mark.asyncio
async def test_suggestions_mutual_dedup_and_popular(async_client: AsyncClient) -> None:
    """Viewer follows A,B. C follows A,B (overlap 2). D follows A only. C ranks above D in mutual.
    Separate author E has recent cards and appears in popular (not in mutual)."""
    ids: dict[int, UUID] = {}
    for tid in (7201, 7202, 7203, 7204, 7205, 7206):
        body = await _login(async_client, telegram_user_id=tid)
        ids[tid] = UUID(str(body['id']))

    v, a, b, c, d, e = ids[7201], ids[7202], ids[7203], ids[7204], ids[7205], ids[7206]

    session_factory = get_session_factory()
    async with session_factory() as session:
        for pair in (
            (v, a),
            (v, b),
            (c, a),
            (c, b),
            (d, a),
        ):
            session.add(
                UserSubscription(
                    id=uuid4(),
                    follower_user_id=pair[0],
                    following_user_id=pair[1],
                )
            )
        film = Film(kinopoisk_id=920_001, title='X', year=None, poster_url=None, genres=[])
        session.add(film)
        await session.flush()
        session.add(
            MovieCard(
                user_id=e,
                film_id=film.id,
                rating=5.0,
                company='solo',
                mood_before='relax',
                mood_after='good',
            )
        )
        await session.commit()

    await _login(async_client, telegram_user_id=7201)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    body = r.json()
    mutual_ids = [u['id'] for u in body['mutual_circle']]
    assert str(c) in mutual_ids
    assert str(d) in mutual_ids
    assert mutual_ids.index(str(c)) < mutual_ids.index(str(d))

    popular_ids = [u['id'] for u in body['popular_authors']]
    assert str(e) in popular_ids
    assert str(c) not in popular_ids
    assert str(d) not in popular_ids

    e_payload = next(u for u in body['popular_authors'] if u['id'] == str(e))
    assert e_payload['movie_cards_count'] == 1
    assert e_payload['average_rating'] == 5.0

    all_ids = (
        mutual_ids
        + [u['id'] for u in body['popular_authors']]
        + [u['id'] for u in body['random_with_cards']]
    )
    assert len(all_ids) == len(set(all_ids))


@pytest.mark.asyncio
async def test_suggestions_popular_peer_not_viewer(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=7301)
    peer = await _login(async_client, telegram_user_id=7302)
    peer_id = UUID(str(peer['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=930_001, title='Y', year=None, poster_url=None, genres=[])
        session.add(film)
        await session.flush()
        session.add(
            MovieCard(
                user_id=peer_id,
                film_id=film.id,
                rating=4.0,
                company='solo',
                mood_before='relax',
                mood_after='ok',
            )
        )
        await session.commit()

    await _login(async_client, telegram_user_id=7301)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    body_out = r.json()
    assert body_out['mutual_circle'] == []
    popular_ids = [u['id'] for u in body_out['popular_authors']]
    assert str(peer_id) in popular_ids


@pytest.mark.asyncio
async def test_suggestions_excludes_already_followed_from_mutual(async_client: AsyncClient) -> None:
    ids: dict[int, UUID] = {}
    for tid in (7401, 7402, 7403):
        body = await _login(async_client, telegram_user_id=tid)
        ids[tid] = UUID(str(body['id']))

    v, a, x = ids[7401], ids[7402], ids[7403]

    session_factory = get_session_factory()
    async with session_factory() as session:
        for pair in ((v, a), (v, x), (x, a)):
            session.add(
                UserSubscription(
                    id=uuid4(),
                    follower_user_id=pair[0],
                    following_user_id=pair[1],
                )
            )
        await session.commit()

    await _login(async_client, telegram_user_id=7401)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    mutual_ids = [u['id'] for u in r.json()['mutual_circle']]
    assert str(x) not in mutual_ids


@pytest.mark.asyncio
async def test_suggestions_excludes_followees_from_popular_and_random(
    async_client: AsyncClient,
) -> None:
    """Users the viewer already follows must not appear in popular or random strips."""
    viewer = await _login(async_client, telegram_user_id=7601)
    peer = await _login(async_client, telegram_user_id=7602)
    viewer_id = UUID(str(viewer['id']))
    peer_id = UUID(str(peer['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            UserSubscription(
                id=uuid4(),
                follower_user_id=viewer_id,
                following_user_id=peer_id,
            )
        )
        film = Film(
            kinopoisk_id=960_001, title='FollowedPeer', year=None, poster_url=None, genres=[]
        )
        session.add(film)
        await session.flush()
        session.add(
            MovieCard(
                user_id=peer_id,
                film_id=film.id,
                rating=4.5,
                company='solo',
                mood_before='relax',
                mood_after='ok',
            )
        )
        await session.commit()

    await _login(async_client, telegram_user_id=7601)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    body = r.json()
    popular_ids = [u['id'] for u in body['popular_authors']]
    random_ids = [u['id'] for u in body['random_with_cards']]
    assert str(peer_id) not in popular_ids
    assert str(peer_id) not in random_ids


@pytest.mark.asyncio
async def test_popular_uses_cards_within_seven_days(async_client: AsyncClient) -> None:
    ids: dict[int, UUID] = {}
    for tid in (7501, 7502):
        body = await _login(async_client, telegram_user_id=tid)
        ids[tid] = UUID(str(body['id']))

    author = ids[7502]

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=950_001, title='Z', year=None, poster_url=None, genres=[])
        session.add(film)
        await session.flush()
        old = MovieCard(
            user_id=author,
            film_id=film.id,
            rating=3.0,
            company='solo',
            mood_before='relax',
            mood_after='meh',
        )
        session.add(old)
        await session.flush()
        old_created = (dt.datetime.now(dt.UTC) - dt.timedelta(days=30)).replace(tzinfo=None)
        await session.execute(
            update(MovieCard).where(MovieCard.id == old.id).values(created_at=old_created)
        )
        await session.commit()

    await _login(async_client, telegram_user_id=7501)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    popular_ids = [u['id'] for u in r.json()['popular_authors']]
    assert str(author) not in popular_ids
