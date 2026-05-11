from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.reaction_type import ReactionType
from models.user import User
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _profile_slug_for_telegram(telegram_user_id: int) -> str:
    session_factory = get_session_factory()
    async with session_factory() as session:
        slug = (
            await session.execute(
                select(User.profile_slug).where(User.telegram_user_id == telegram_user_id)
            )
        ).scalar_one()
        return str(slug)


async def _insert_reaction_type(*, asset_key: str) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        rt = ReactionType(
            category_slug='smiles',
            asset_key=asset_key,
            image_url='https://example.com/reaction.png',
        )
        session.add(rt)
        await session.commit()
        await session.refresh(rt)
        return int(rt.id)


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
        session.add(user)
        await session.flush()
        film = Film(
            kinopoisk_id=100700,
            title='Оппенгеймер',
            year=2023,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user.id,
            film_id=film.id,
            rating=8.5,
            company='alone',
            mood_before='thrill',
            mood_after='tense',
        )
        session.add(card)
        await session.commit()
        card_id = card.id

    r = await async_client.get(f'/api/cards/{card_id}')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_card_success_surfaces_movie_and_author(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=621)
    film = await _create_film(kinopoisk_id=100621)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['боевик'],
            'rating': 8.0,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    fetched = await async_client.get(f'/api/cards/{card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['id'] == card_id
    assert body['user_id'] == data['id']
    assert body['is_favorite'] is False
    assert body['film_kinopoisk_id'] == film.kinopoisk_id
    assert body['film_title'] == 'Интерстеллар'
    assert body['card_author']['id'] == data['id']
    assert body['card_author']['profile_slug']
    assert body['watch_note'] == ''
    assert 'reactions' in body


@pytest.mark.asyncio
async def test_create_card_watch_note_roundtrip(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=629)
    film = await _create_film(kinopoisk_id=100629)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
            'watch_note': '  Сильный финал 🔥  ',
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    fetched = await async_client.get(f'/api/cards/{card_id}')
    assert fetched.status_code == 200
    detail = fetched.json()
    assert detail['watch_note'] == 'Сильный финал 🔥'
    assert detail['reactions']['counts'] == []
    assert detail['reactions']['my_reaction_type_ids'] == []


@pytest.mark.asyncio
async def test_get_card_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=622)
    r = await async_client.get('/api/cards/999999')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_card_requires_auth(async_client: AsyncClient) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        from models.user import User

        user = User(
            telegram_user_id=777001,
            profile_slug='anon-patch-card-test',
            username='patch_tester',
            first_name='Patch',
            last_name='Tester',
            photo_url=None,
            display_name='Patch Tester',
            bio=None,
            language_code='ru',
        )
        session.add(user)
        await session.flush()
        film = Film(
            kinopoisk_id=100701,
            title='Тест',
            year=2000,
            poster_url='https://example.com/poster.jpg',
            genres=[],
        )
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user.id,
            film_id=film.id,
            rating=6.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        card_id = card.id

    r = await async_client.patch(f'/api/cards/{card_id}', json={'rating': 7.0})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_patch_card_success(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=623)
    film = await _create_film(kinopoisk_id=100623)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 5.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    patched = await async_client.patch(f'/api/cards/{card_id}', json={'rating': 7.5})
    assert patched.status_code == 200
    assert patched.json()['rating'] == 7.5


@pytest.mark.asyncio
async def test_patch_card_watch_note(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=628)
    film = await _create_film(kinopoisk_id=100628)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
            'watch_note': 'старое',
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    patched = await async_client.patch(f'/api/cards/{card_id}', json={'watch_note': ''})
    assert patched.status_code == 200
    got = await async_client.get(f'/api/cards/{card_id}')
    assert got.json()['watch_note'] == ''


@pytest.mark.asyncio
async def test_patch_card_forbidden_for_another_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=624)
    film = await _create_film(kinopoisk_id=100624)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    await _login(async_client, telegram_user_id=625)
    blocked = await async_client.patch(f'/api/cards/{card_id}', json={'rating': 9.0})
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_patch_card_is_favorite_toggle(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=9601)
    film = await _create_film(kinopoisk_id=199601)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    assert created.json()['is_favorite'] is False

    fav = await async_client.patch(f'/api/cards/{card_id}', json={'is_favorite': True})
    assert fav.status_code == 200
    assert fav.json()['is_favorite'] is True
    got = await async_client.get(f'/api/cards/{card_id}')
    assert got.json()['is_favorite'] is True

    unfav = await async_client.patch(f'/api/cards/{card_id}', json={'is_favorite': False})
    assert unfav.status_code == 200
    assert unfav.json()['is_favorite'] is False
    got2 = await async_client.get(f'/api/cards/{card_id}')
    assert got2.json()['is_favorite'] is False


@pytest.mark.asyncio
async def test_patch_card_foreign_user_cannot_toggle_favorite(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=9602)
    film = await _create_film(kinopoisk_id=199602)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    await _login(async_client, telegram_user_id=9603)
    blocked = await async_client.patch(f'/api/cards/{card_id}', json={'is_favorite': True})
    assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_delete_card_requires_auth(async_client: AsyncClient) -> None:
    film = await _create_film(kinopoisk_id=100626)
    session_factory = get_session_factory()
    async with session_factory() as session:
        from models.user import User

        user = User(
            telegram_user_id=726,
            profile_slug='delete-card-requires-auth-owner',
            username='del_req',
            first_name='D',
            last_name='R',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.flush()
        card = MovieCard(
            user_id=user.id,
            film_id=film.id,
            rating=7.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        cid = card.id

    deleted = await async_client.delete(f'/api/cards/{cid}')
    assert deleted.status_code == 401


@pytest.mark.asyncio
async def test_delete_card_success_owner(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=727)
    film = await _create_film(kinopoisk_id=100727, title='Одержимость', year=2014)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 9.0,
            'company': 'alone',
            'mood_before': 'thrill',
            'mood_after': 'enjoyed',
            'custom_tags': ['джаз'],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    root = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'Сильный финал'},
    )
    assert root.status_code == 200

    deleted = await async_client.delete(f'/api/cards/{card_id}')
    assert deleted.status_code == 204

    details = await async_client.get(f'/api/cards/{card_id}')
    assert details.status_code == 404

    comments = await async_client.get(f'/api/cards/{card_id}/comments')
    assert comments.status_code == 404


@pytest.mark.asyncio
async def test_delete_card_forbidden_for_another_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=728)
    film = await _create_film(kinopoisk_id=100728, title='Семь', year=1995)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['триллер'],
            'rating': 8.5,
            'company': 'friends',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    await _login(async_client, telegram_user_id=729)
    forbidden = await async_client.delete(f'/api/cards/{card_id}')
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_delete_card_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=730)
    response = await async_client.delete('/api/cards/999999')
    assert response.status_code == 404


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
    assert 'reactions' in root_body

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

    listed = await async_client.get(f'/api/cards/{card_id}/comments')
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body['next_cursor'] is None
    items = listed_body['items']
    assert len(items) == 3
    for it in items:
        assert 'reactions' in it

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
    assert (
        reply_items[0]['id'],
        reply_items[0]['replies_count'],
        reply_items[0]['total_descendants_count'],
    ) == (
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
async def test_comment_reaction_embedded_tokens(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=707)
    film = await _create_film(kinopoisk_id=100707, title='Токены', year=2020)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    rx1 = await _insert_reaction_type(asset_key='comment-embed-707-a')
    ok = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': f'вау ⟦r{rx1}⟧ класс'},
    )
    assert ok.status_code == 200
    assert ok.json()['text'] == f'вау ⟦r{rx1}⟧ класс'

    bad = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': '⟦r999999999⟧ нет'},
    )
    assert bad.status_code == 422

    rx2 = await _insert_reaction_type(asset_key='comment-embed-707-b')
    rx3 = await _insert_reaction_type(asset_key='comment-embed-707-c')
    rx4 = await _insert_reaction_type(asset_key='comment-embed-707-d')
    many_tokens = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': f'⟦r{rx1}⟧⟦r{rx2}⟧⟦r{rx3}⟧⟦r{rx4}⟧ много'},
    )
    assert many_tokens.status_code == 200


@pytest.mark.asyncio
async def test_comment_mention_follower_token_ok(async_client: AsyncClient) -> None:
    author = await _login(async_client, telegram_user_id=90220)
    target = await _login(async_client, telegram_user_id=90221)
    slug_target = await _profile_slug_for_telegram(90221)
    await _login(async_client, telegram_user_id=90220)
    await async_client.post(f'/api/users/{target["id"]}/subscriptions')

    film = await _create_film(kinopoisk_id=100902, title='Упоминание', year=2022)
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

    r = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': f'привет ⟦@{slug_target}⟧'},
    )
    assert r.status_code == 200
    assert '⟦@' in r.json()['text'] and slug_target.lower() in r.json()['text'].lower()
    assert r.json()['author']['id'] == author['id']


@pytest.mark.asyncio
async def test_comment_mention_not_following_rejected(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=90222)
    await _login(async_client, telegram_user_id=90223)
    slug_other = await _profile_slug_for_telegram(90223)
    await _login(async_client, telegram_user_id=90222)

    film = await _create_film(kinopoisk_id=100903, title='Без подписки', year=2021)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    r = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': f'⟦@{slug_other}⟧'},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_comment_create_requires_auth_and_read_requires_auth(
    async_client: AsyncClient,
) -> None:
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

    unauth_read = await async_client.get(f'/api/cards/{card_id}/comments')
    assert unauth_read.status_code == 401


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

    resolved_again = await async_client.post(
        '/api/films/resolve',
        json={'url': 'https://www.kinopoisk.ru/film/301/'},
    )
    assert resolved_again.status_code == 200
    assert resolved_again.json()['id'] == body['id']
    assert resolved_again.json().get('my_card_id') in (None, 0)


@pytest.mark.asyncio
async def test_get_film_includes_my_card_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=623)
    film = await _create_film(kinopoisk_id=100623)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    fetched = await async_client.get(f'/api/films/{film.id}')
    assert fetched.status_code == 200
    assert fetched.json()['my_card_id'] == card_id


@pytest.mark.asyncio
async def test_resolve_film_series_url(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=620)

    async def fake_get_film(self: object, kinopoisk_id: int):
        from services.kinopoisk.client import KinopoiskFilmPayload

        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title='Сериал-тест',
            year=2024,
            poster_url=None,
            genres=['драма'],
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    resolved = await async_client.post(
        '/api/films/resolve',
        json={'url': 'https://www.kinopoisk.ru/series/404900/'},
    )
    assert resolved.status_code == 200
    assert resolved.json()['kinopoisk_id'] == 404900
    assert resolved.json()['title'] == 'Сериал-тест'


@pytest.mark.asyncio
async def test_resolve_film_invalid_url(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=617)
    r = await async_client.post('/api/films/resolve', json={'url': 'https://example.com/not-kino'})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_card_model_uses_unique_user_film_pair() -> None:
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


@pytest.mark.asyncio
async def test_movie_card_feed_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/cards/feed')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_movie_card_feed_includes_comments_count_and_preview(
    async_client: AsyncClient,
) -> None:
    viewer = await _login(async_client, telegram_user_id=916)
    author = await _login(async_client, telegram_user_id=9160)
    await _login(async_client, telegram_user_id=916)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')
    await _login(async_client, telegram_user_id=9160)

    film = await _create_film(kinopoisk_id=100916)
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 8.5,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'laughed',
            'custom_tags': ['a', 'b'],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']

    for label in ('c1', 'c2', 'c3'):
        c = await async_client.post(f'/api/cards/{card_id}/comments', json={'text': label})
        assert c.status_code == 200

    await _login(async_client, telegram_user_id=916)
    feed = await async_client.get('/api/cards/feed?limit=50')
    assert feed.status_code == 200
    body = feed.json()
    ours = next((item for item in body['items'] if item['id'] == card_id), None)
    assert ours is not None
    assert ours['user_id'] == author['id']
    assert ours['comments_count'] == 3
    assert ours['feed_source'] in ('subscriptions', 'personal_affinity')
    assert ours['card_author']['id'] == author['id']
    assert 'reactions' in ours
    previews = ours['comments_preview']
    assert len(previews) == 3
    assert [p['text'] for p in previews] == ['c1', 'c2', 'c3']
    for p in previews:
        assert 'reactions' in p
    assert viewer['id'] != author['id']


@pytest.mark.asyncio
async def test_movie_card_feed_cursor_pagination(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=917)
    author_a = await _login(async_client, telegram_user_id=9170)
    author_b = await _login(async_client, telegram_user_id=9171)
    await _login(async_client, telegram_user_id=917)
    await async_client.post(f'/api/users/{author_a["id"]}/subscriptions')
    await async_client.post(f'/api/users/{author_b["id"]}/subscriptions')

    card_ids: list[int] = []
    for telegram_uid, kid in ((9170, 1009171), (9171, 1009172)):
        await _login(async_client, telegram_user_id=telegram_uid)
        film = await _create_film(kinopoisk_id=kid, title=f'Film {kid}')
        r = await async_client.post(
            '/api/cards',
            json={
                'film_id': film.id,
                'kinopoisk_id': film.kinopoisk_id,
                'genres': [],
                'rating': 8.0,
                'company': 'alone',
                'mood_before': 'relax',
                'mood_after': 'enjoyed',
                'custom_tags': [],
            },
        )
        assert r.status_code == 200
        card_ids.append(r.json()['id'])

    await _login(async_client, telegram_user_id=917)
    first_page = await async_client.get('/api/cards/feed?limit=1&mode=subscriptions_only')
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body['items']) == 1
    first_id = first_body['items'][0]['id']
    assert first_id in card_ids
    assert first_body.get('next_cursor') is not None

    second_page = await async_client.get(
        f'/api/cards/feed?limit=1&mode=subscriptions_only&cursor={first_body["next_cursor"]}'
    )
    assert second_page.status_code == 200
    second_body = second_page.json()
    assert len(second_body['items']) == 1
    second_id = second_body['items'][0]['id']
    assert second_id in card_ids
    assert second_id != first_id
