"""Collections HTTP API routes."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.collection import Collection, CollectionKind
from models.collection_film import CollectionFilm
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.collections.pin_collection import MAX_COLLECTION_PINS
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'colapi-{telegram_user_id}',
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
    film_ids: list[int],
    kind: CollectionKind = CollectionKind.evergreen,
    is_active: bool = True,
) -> Collection:
    session_factory = get_session_factory()
    async with session_factory() as session:
        collection = Collection(
            slug=slug,
            kind=kind,
            title=f'Title {slug}',
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


async def _rate_film(*, user_id: UUID, film: Film, rating: float = 8.0) -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        category_id = await ensure_default_category(session, user_id)
        existing_catalog = (
            await session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == film.id),
            )
        ).scalar_one_or_none()
        if existing_catalog is not None:
            catalog_item_id = int(existing_catalog)
        else:
            catalog = CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                film_id=film.id,
            )
            session.add(catalog)
            await session.flush()
            catalog_item_id = int(catalog.id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            catalog_item_id=catalog_item_id,
            provider=CatalogProvider.kinopoisk,
            category_id=category_id,
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card


@pytest.mark.asyncio
async def test_list_collections_guest_and_auth(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    slug = f'test-list-{suffix}'
    film = await _create_film(kinopoisk_id=2_000_000 + suffix, title='List Film')
    await _create_collection_with_films(slug=slug, film_ids=[int(film.id)])

    guest = await async_client.get('/api/collections')
    assert guest.status_code == 200
    guest_body = guest.json()
    assert 'items' in guest_body
    guest_item = next((it for it in guest_body['items'] if it['slug'] == slug), None)
    assert guest_item is not None
    assert guest_item['viewer_progress'] is None
    assert guest_item['is_pinned'] is None
    assert guest_item['film_count'] == 1

    tg_id = 9_000_000 + suffix
    await _create_user(telegram_user_id=tg_id)
    await _login(async_client, tg_id)
    authed = await async_client.get('/api/collections')
    assert authed.status_code == 200
    authed_item = next((it for it in authed.json()['items'] if it['slug'] == slug), None)
    assert authed_item is not None
    assert authed_item['viewer_progress'] == {
        'rated_count': 0,
        'total_count': 1,
        'completed_at': None,
    }
    assert authed_item['is_pinned'] is False


@pytest.mark.asyncio
async def test_get_collection_by_slug_not_found(async_client: AsyncClient) -> None:
    response = await async_client.get('/api/collections/does-not-exist-slug')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_collection_films_pagination_and_viewer_has_rated(
    async_client: AsyncClient,
) -> None:
    suffix = uuid4().int % 1_000_000
    slug = f'test-films-{suffix}'
    films = [
        await _create_film(kinopoisk_id=3_000_000 + suffix + i, title=f'Film {i}') for i in range(3)
    ]
    await _create_collection_with_films(slug=slug, film_ids=[int(f.id) for f in films])

    tg_id = 9_100_000 + suffix
    user = await _create_user(telegram_user_id=tg_id)
    await _rate_film(user_id=user.id, film=films[0])
    await _login(async_client, tg_id)

    page1 = await async_client.get('/api/collections/' + slug + '/films', params={'limit': 2})
    assert page1.status_code == 200
    body1 = page1.json()
    assert body1['total_count'] == 3
    assert len(body1['items']) == 2
    assert body1['next_cursor'] is not None
    assert body1['items'][0]['viewer_has_rated'] is True
    assert body1['items'][0]['viewer_card_id'] is not None
    assert body1['items'][1]['viewer_has_rated'] is False
    assert body1['items'][1]['viewer_card_id'] is None

    page2 = await async_client.get(
        '/api/collections/' + slug + '/films',
        params={'limit': 2, 'cursor': body1['next_cursor']},
    )
    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2['items']) == 1
    assert body2['next_cursor'] is None


@pytest.mark.asyncio
async def test_pin_unpin_and_max_limit(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    tg_id = 9_200_000 + suffix
    await _create_user(telegram_user_id=tg_id)
    await _login(async_client, tg_id)

    slugs: list[str] = []
    for i in range(MAX_COLLECTION_PINS + 1):
        slug = f'pin-{suffix}-{i}'
        film = await _create_film(kinopoisk_id=4_000_000 + suffix + i, title=f'Pin Film {i}')
        await _create_collection_with_films(slug=slug, film_ids=[int(film.id)])
        slugs.append(slug)

    first_slug = slugs[0]
    pin = await async_client.post(f'/api/me/collection-pins/{first_slug}')
    assert pin.status_code == 204

    pin_again = await async_client.post(f'/api/me/collection-pins/{first_slug}')
    assert pin_again.status_code == 204

    for slug in slugs[1:MAX_COLLECTION_PINS]:
        response = await async_client.post(f'/api/me/collection-pins/{slug}')
        assert response.status_code == 204

    over = await async_client.post(f'/api/me/collection-pins/{slugs[MAX_COLLECTION_PINS]}')
    assert over.status_code == 409

    unpin = await async_client.delete(f'/api/me/collection-pins/{first_slug}')
    assert unpin.status_code == 204
    unpin_again = await async_client.delete(f'/api/me/collection-pins/{first_slug}')
    assert unpin_again.status_code == 204


@pytest.mark.asyncio
async def test_profile_pinned_collections_empty_and_populated(
    async_client: AsyncClient,
) -> None:
    suffix = uuid4().int % 1_000_000
    tg_id = 9_300_000 + suffix
    user = await _create_user(telegram_user_id=tg_id)

    empty = await async_client.get(f'/api/profiles/{user.id}/collections')
    assert empty.status_code == 200
    assert empty.json()['items'] == []

    slug_a = f'profile-a-{suffix}'
    slug_b = f'profile-b-{suffix}'
    film_a = await _create_film(kinopoisk_id=5_000_000 + suffix, title='Profile A')
    film_b = await _create_film(kinopoisk_id=5_000_001 + suffix, title='Profile B')
    await _create_collection_with_films(slug=slug_a, film_ids=[int(film_a.id)])
    await _create_collection_with_films(slug=slug_b, film_ids=[int(film_b.id)])

    await _login(async_client, tg_id)
    assert (await async_client.post(f'/api/me/collection-pins/{slug_b}')).status_code == 204
    assert (await async_client.post(f'/api/me/collection-pins/{slug_a}')).status_code == 204

    populated = await async_client.get(f'/api/profiles/{user.id}/collections')
    assert populated.status_code == 200
    items = populated.json()['items']
    assert len(items) == 2
    assert items[0]['slug'] == slug_b
    assert items[1]['slug'] == slug_a
    assert items[0]['is_pinned'] is True
    assert items[0]['viewer_progress']['rated_count'] == 0

    missing_user = await async_client.get(f'/api/profiles/{uuid4()}/collections')
    assert missing_user.status_code == 404
