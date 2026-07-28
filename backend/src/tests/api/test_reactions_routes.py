from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.reaction_type import ReactionType
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _seed_reaction_catalog() -> tuple[int, int, int]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                ReactionType(
                    image_url='https://example.com/a.png',
                    category_slug='pepe',
                    asset_key='reactions/pepe/a.png',
                ),
                ReactionType(
                    image_url='https://example.com/b.png',
                    category_slug='meme_pt1',
                    asset_key='reactions/meme_pt1/b.png',
                ),
                ReactionType(
                    image_url='https://example.com/c.png',
                    category_slug='cats',
                    asset_key='reactions/cats/c.png',
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        active_ids = (
            (await session.execute(select(ReactionType.id).order_by(ReactionType.id.asc())))
            .scalars()
            .all()
        )
        assert len(active_ids) >= 3
        return (int(active_ids[0]), int(active_ids[1]), int(active_ids[2]))


async def _create_card_any(async_client: AsyncClient, tg: int, kid: int) -> int:
    await _login(async_client, telegram_user_id=tg)
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kid,
            title=f'Rf {kid}',
            year=2021,
            poster_url=None,
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id_val = film.id
        kop = film.kinopoisk_id
    card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film_id_val,
            'kinopoisk_id': kop,
            'genres': ['драма'],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert card.status_code == 200
    return int(card.json()['id'])


@pytest.mark.asyncio
async def test_reactions_catalog_requires_auth(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    assert (await async_client.get('/api/reactions/catalog')).status_code == 401


@pytest.mark.asyncio
async def test_reactions_set_requires_auth(async_client: AsyncClient) -> None:
    tid, *_ = await _seed_reaction_catalog()
    r = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': 1, 'reaction_type_id': tid},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_reactions_catalog_ordered_tabs(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    await _login(async_client, telegram_user_id=940)
    resp = await async_client.get('/api/reactions/catalog')
    assert resp.status_code == 200
    body = resp.json()
    assert len(body['tabs']) == 5
    assert sum(len(t['items']) for t in body['tabs']) == 3


@pytest.mark.asyncio
async def test_reactions_catalog_misc_tab_includes_unknown_slug(async_client: AsyncClient) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            ReactionType(
                image_url='https://example.com/s.png',
                category_slug='misc',
                asset_key='reactions/misc/solo.png',
            )
        )
        await session.commit()
    await _login(async_client, telegram_user_id=951)
    resp = await async_client.get('/api/reactions/catalog')
    assert resp.status_code == 200
    tabs = resp.json()['tabs']
    misc = next((t for t in tabs if t['category_slug'] == 'misc'), None)
    assert misc is not None
    assert len(misc['items']) == 1
    assert misc['items'][0]['asset_key'] == 'reactions/misc/solo.png'


@pytest.mark.asyncio
async def test_set_reaction_multiple_per_target_toggle(async_client: AsyncClient) -> None:
    a, b, c = await _seed_reaction_catalog()
    cid = await _create_card_any(async_client, 941, 941_941)
    await _login(async_client, telegram_user_id=941)

    r1 = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    assert r1.status_code == 200
    assert set(r1.json()['reactions']['my_reaction_type_ids']) == {a}
    rx_body = r1.json()['reactions']
    assert len(rx_body['counts']) == 1
    assert rx_body['counts'][0]['count'] == 1
    assert len(rx_body['counts'][0]['reactors']) == 1

    card = await async_client.get(f'/api/cards/{cid}')
    assert card.status_code == 200
    assert set(card.json()['reactions']['my_reaction_type_ids']) == {a}
    assert len(card.json()['reactions']['counts'][0]['reactors']) == 1

    # same type again -> remove that reaction only
    r_same = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    assert r_same.status_code == 200
    assert r_same.json()['reactions']['my_reaction_type_ids'] == []

    await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    rb = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': b},
    )
    assert rb.status_code == 200
    assert set(rb.json()['reactions']['my_reaction_type_ids']) == {a, b}

    missing_type = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': 990_991},
    )
    assert missing_type.status_code == 422

    missing_card = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': 991_991_991, 'reaction_type_id': c},
    )
    assert missing_card.status_code == 404

    bad_kind = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'nope', 'target_id': cid, 'reaction_type_id': c},
    )
    assert bad_kind.status_code == 422


@pytest.mark.asyncio
async def test_reactions_actors_requires_auth(async_client: AsyncClient) -> None:
    tid, *_ = await _seed_reaction_catalog()
    r = await async_client.get(
        '/api/reactions/actors',
        params={
            'target_kind': 'movie_card',
            'target_id': 1,
            'reaction_type_id': tid,
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_reactions_actors_returns_reactors(async_client: AsyncClient) -> None:
    rx, *_ = await _seed_reaction_catalog()
    cid = await _create_card_any(async_client, 944, 944_944)
    await _login(async_client, telegram_user_id=945)
    post = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': rx},
    )
    assert post.status_code == 200
    me = await async_client.get('/api/me')
    assert me.status_code == 200
    user_id_str = me.json()['id']

    act = await async_client.get(
        '/api/reactions/actors',
        params={
            'target_kind': 'movie_card',
            'target_id': cid,
            'reaction_type_id': rx,
        },
    )
    assert act.status_code == 200
    items = act.json()['items']
    assert len(items) == 1
    assert str(items[0]['id']) == user_id_str


@pytest.mark.asyncio
async def test_set_reaction_on_comment(async_client: AsyncClient) -> None:
    rx1, *_ = await _seed_reaction_catalog()
    cid = await _create_card_any(async_client, 942, kid=942_942)
    await _login(async_client, telegram_user_id=942)
    cm = await async_client.post(f'/api/cards/{cid}/comments', json={'text': 'hi'})
    assert cm.status_code == 200
    com_id = cm.json()['id']

    rr = await async_client.post(
        '/api/reactions',
        json={
            'target_kind': 'movie_card_comment',
            'target_id': com_id,
            'reaction_type_id': rx1,
        },
    )
    assert rr.status_code == 200
    lst = await async_client.get(f'/api/cards/{cid}/comments')
    assert lst.status_code == 200
    reactions = lst.json()['items'][0]['reactions']
    assert reactions['my_reaction_type_ids'] == [rx1]
    assert reactions['counts'] and reactions['counts'][0]['count'] == 1
    assert len(reactions['counts'][0]['reactors']) == 1

    nf = await async_client.post(
        '/api/reactions',
        json={
            'target_kind': 'movie_card_comment',
            'target_id': 999998,
            'reaction_type_id': rx1,
        },
    )
    assert nf.status_code == 404
