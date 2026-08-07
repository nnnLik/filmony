"""GET /api/films/{film_id}/collections — collections that include a film."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.collection import Collection, CollectionKind
from models.collection_film import CollectionFilm
from models.film import Film
from models.user import User
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'filmcol-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int, title: str) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2020,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _create_collection_with_films(
    *,
    slug: str,
    title: str,
    film_ids: list[int],
    kind: CollectionKind = CollectionKind.evergreen,
    is_active: bool = True,
) -> Collection:
    session_factory = get_session_factory()
    async with session_factory() as session:
        collection = Collection(
            slug=slug,
            kind=kind,
            title=title,
            description=f'Description {slug}',
            film_count=len(film_ids),
            is_active=is_active,
        )
        session.add(collection)
        await session.flush()
        for index, film_id in enumerate(film_ids):
            session.add(
                CollectionFilm(
                    collection_id=collection.id,
                    film_id=film_id,
                    sort_order=index,
                )
            )
        await session.commit()
        await session.refresh(collection)
        return collection


@pytest.mark.asyncio
async def test_list_film_collections_empty_and_membership(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    user = await _create_user(telegram_user_id=9_100_000 + suffix)
    await _login(async_client, int(user.telegram_user_id))

    film_a = await _create_film(kinopoisk_id=8_100_000 + suffix, title=f'Film A {suffix}')
    film_b = await _create_film(kinopoisk_id=8_200_000 + suffix, title=f'Film B {suffix}')

    await _create_collection_with_films(
        slug=f'zebra-{suffix}',
        title=f'Zebra {suffix}',
        film_ids=[film_a.id],
    )
    await _create_collection_with_films(
        slug=f'alpha-{suffix}',
        title=f'Alpha {suffix}',
        film_ids=[film_a.id, film_b.id],
    )
    await _create_collection_with_films(
        slug=f'inactive-{suffix}',
        title=f'Inactive {suffix}',
        film_ids=[film_a.id],
        is_active=False,
    )
    await _create_collection_with_films(
        slug=f'other-{suffix}',
        title=f'Other {suffix}',
        film_ids=[film_b.id],
    )

    empty = await async_client.get(f'/api/films/{film_b.id + 999_999}/collections')
    assert empty.status_code == 404

    for_b = await async_client.get(f'/api/films/{film_b.id}/collections')
    assert for_b.status_code == 200
    b_slugs = [item['slug'] for item in for_b.json()['items']]
    assert b_slugs == [f'alpha-{suffix}', f'other-{suffix}']
    assert for_b.json()['items'][0]['viewer_progress'] is not None
    assert for_b.json()['items'][0]['is_pinned'] is False

    for_a = await async_client.get(f'/api/films/{film_a.id}/collections')
    assert for_a.status_code == 200
    a_slugs = [item['slug'] for item in for_a.json()['items']]
    assert a_slugs == [f'alpha-{suffix}', f'zebra-{suffix}']
    assert f'inactive-{suffix}' not in a_slugs


@pytest.mark.asyncio
async def test_list_film_collections_no_membership(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    user = await _create_user(telegram_user_id=9_200_000 + suffix)
    await _login(async_client, int(user.telegram_user_id))
    film = await _create_film(kinopoisk_id=8_300_000 + suffix, title=f'Lonely {suffix}')

    response = await async_client.get(f'/api/films/{film.id}/collections')
    assert response.status_code == 200
    assert response.json() == {'items': []}
