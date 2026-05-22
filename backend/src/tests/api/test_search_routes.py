from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


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
async def test_search_returns_matching_cards_users_and_film_alias(async_client: AsyncClient) -> None:
    viewer = await _login(async_client, telegram_user_id=7102)
    owner_a = await _login(async_client, telegram_user_id=7103)
    owner_b = await _login(async_client, telegram_user_id=7104)
    viewer_id = UUID(str(viewer['id']))
    owner_a_id = UUID(str(owner_a['id']))
    owner_b_id = UUID(str(owner_b['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=910_001,
            title='УникальныйТайтлПоиска',
            year=2020,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
            short_description='Краткий синопсис карточки фильма',
            description='Полное описание карточки фильма',
        )
        session.add(film)
        await session.flush()
        cat_a = await ensure_default_category(session, owner_a_id)
        cat_b = await ensure_default_category(session, owner_b_id)
        film_card = UserCard(
            user_id=owner_a_id,
            film_id=film.id,
            category_id=cat_a,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=7.5,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        manual_card = UserCard(
            user_id=owner_b_id,
            film_id=None,
            catalog_item_id=None,
            category_id=cat_b,
            provider=CatalogProvider.no_provider,
            external_id=None,
            display_title='РучнойТайтлПоиска',
            display_cover_url='https://example.com/manual.jpg',
            display_summary='Ручное описание карточки',
            rating=8.0,
            company='friends',
            mood_before='laugh',
            mood_after='enjoyed',
        )
        session.add_all([film_card, manual_card])
        await session.flush()
        film_card_id = film_card.id
        manual_card_id = manual_card.id
        viewer_row = await session.execute(select(User).where(User.id == viewer_id))
        me = viewer_row.scalar_one()
        me.display_name = 'УникальныйТайтлПоиска Пользователь'
        session.add(me)
        await session.commit()

    r = await async_client.get('/api/search', params={'q': 'ТайтлПоиска'})
    assert r.status_code == 200
    body = r.json()
    card_ids = {c['card_id'] for c in body['cards']}
    assert {film_card_id, manual_card_id}.issubset(card_ids)
    assert body['films'] == body['cards']
    manual_hit = next(c for c in body['cards'] if c['card_id'] == manual_card_id)
    assert manual_hit['title'] == 'РучнойТайтлПоиска'
    assert manual_hit['summary'] == 'Ручное описание карточки'
    assert manual_hit['poster_url'] == 'https://example.com/manual.jpg'
    assert manual_hit['author_profile_slug']
    assert any(u['id'] == str(viewer_id) for u in body['users'])


@pytest.mark.asyncio
async def test_search_matches_manual_card_display_title_without_film(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=7110)
    uid = UUID(str(data['id']))
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, uid)
        manual = UserCard(
            user_id=uid,
            film_id=None,
            catalog_item_id=None,
            category_id=cat_id,
            provider=CatalogProvider.no_provider,
            external_id=None,
            display_title='РучнойТайтлПоискаXyz',
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(manual)
        await session.flush()
        card_id = manual.id
        await session.commit()

    r = await async_client.get('/api/search', params={'q': 'РучнойТай'})
    assert r.status_code == 200
    body = r.json()
    assert any(c['card_id'] == card_id for c in body['cards'])
    assert any(f['card_id'] == card_id for f in body['films'])

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
        cat_e = await ensure_default_category(session, e)
        session.add(
            UserCard(
                user_id=e,
                film_id=film.id,
                category_id=cat_e,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
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
        cat_peer = await ensure_default_category(session, peer_id)
        session.add(
            UserCard(
                user_id=peer_id,
                film_id=film.id,
                category_id=cat_peer,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
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
        cat_peer = await ensure_default_category(session, peer_id)
        session.add(
            UserCard(
                user_id=peer_id,
                film_id=film.id,
                category_id=cat_peer,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
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
        cat_author = await ensure_default_category(session, author)
        old = UserCard(
            user_id=author,
            film_id=film.id,
            category_id=cat_author,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=3.0,
            company='solo',
            mood_before='relax',
            mood_after='meh',
        )
        session.add(old)
        await session.flush()
        old_created = (dt.datetime.now(dt.UTC) - dt.timedelta(days=30)).replace(tzinfo=None)
        await session.execute(
            update(UserCard).where(UserCard.id == old.id).values(created_at=old_created)
        )
        await session.commit()

    await _login(async_client, telegram_user_id=7501)
    r = await async_client.get('/api/search/suggestions')
    assert r.status_code == 200
    popular_ids = [u['id'] for u in r.json()['popular_authors']]
    assert str(author) not in popular_ids
