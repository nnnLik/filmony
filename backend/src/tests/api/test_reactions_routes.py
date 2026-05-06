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


async def _seed_reaction_catalog() -> tuple[int, int, int, int]:
    """(active_low, active_mid, active_high, inactive_id)."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                ReactionType(
                    label='A',
                    image_url='https://example.com/a.png',
                    sort_order=1,
                    category_slug='pepe',
                    is_active=True,
                ),
                ReactionType(
                    label='B',
                    image_url='https://example.com/b.png',
                    sort_order=2,
                    category_slug='meme_pt1',
                    is_active=True,
                ),
                ReactionType(
                    label='C',
                    image_url='https://example.com/c.png',
                    sort_order=3,
                    category_slug='cats',
                    is_active=True,
                ),
                ReactionType(
                    label='Zombie',
                    image_url='https://example.com/z.png',
                    sort_order=100,
                    category_slug='frieren',
                    is_active=False,
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        active_ids = (
            (
                await session.execute(
                    select(ReactionType.id)
                    .where(ReactionType.is_active.is_(True))
                    .order_by(ReactionType.sort_order.asc())
                )
            )
            .scalars()
            .all()
        )
        inactive_id = (
            await session.execute(
                select(ReactionType.id).where(ReactionType.is_active.is_(False)).limit(1)
            )
        ).scalar_one()
        assert len(active_ids) >= 3
        return (int(active_ids[0]), int(active_ids[1]), int(active_ids[2]), int(inactive_id))


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
async def test_reactions_catalog_active_only_ordered(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    await _login(async_client, telegram_user_id=940)
    resp = await async_client.get('/api/reactions/catalog')
    assert resp.status_code == 200
    body = resp.json()
    assert len(body['tabs']) == 5
    assert sum(len(t['items']) for t in body['tabs']) == 3
    assert body['recent'] == []
    assert all((x.get('label') or '') != 'Zombie' for tab in body['tabs'] for x in tab['items'])


@pytest.mark.asyncio
async def test_reactions_catalog_misc_tab_includes_orphans(async_client: AsyncClient) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            ReactionType(
                label='Solo',
                image_url='https://example.com/s.png',
                sort_order=5,
                category_slug=None,
                is_active=True,
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
    assert misc['items'][0]['label'] == 'Solo'


@pytest.mark.asyncio
async def test_set_reaction_on_card_toggle_replace_validate(async_client: AsyncClient) -> None:
    a, b, c, off = await _seed_reaction_catalog()
    cid = await _create_card_any(async_client, 941, 941_941)
    await _login(async_client, telegram_user_id=941)

    r1 = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    assert r1.status_code == 200
    body = await async_client.get(f'/api/cards/{cid}')
    assert body.status_code == 200
    assert body.json()['reactions']['my_reaction_type_id'] == a

    r_same = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    assert r_same.status_code == 200
    assert r_same.json()['reactions']['my_reaction_type_id'] is None

    await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    rb = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': b},
    )
    assert rb.status_code == 200
    assert rb.json()['reactions']['my_reaction_type_id'] == b

    inactive = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': off},
    )
    assert inactive.status_code == 422

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
async def test_reactions_catalog_recent_after_post(async_client: AsyncClient) -> None:
    a, *_rest = await _seed_reaction_catalog()
    cid = await _create_card_any(async_client, 943, 943_943)
    cat0 = await async_client.get('/api/reactions/catalog')
    assert cat0.status_code == 200
    assert cat0.json()['recent'] == []

    rr = await async_client.post(
        '/api/reactions',
        json={'target_kind': 'movie_card', 'target_id': cid, 'reaction_type_id': a},
    )
    assert rr.status_code == 200

    cat1 = await async_client.get('/api/reactions/catalog')
    assert cat1.status_code == 200
    recent = cat1.json()['recent']
    assert len(recent) == 1
    assert recent[0]['id'] == a


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
    assert reactions['my_reaction_type_id'] == rx1
    assert reactions['counts'] and reactions['counts'][0]['count'] == 1

    nf = await async_client.post(
        '/api/reactions',
        json={
            'target_kind': 'movie_card_comment',
            'target_id': 999998,
            'reaction_type_id': rx1,
        },
    )
    assert nf.status_code == 404
