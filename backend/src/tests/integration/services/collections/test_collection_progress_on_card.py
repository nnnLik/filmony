"""Integration coverage for collection progress refresh on card changes."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogProvider
from models.collection import Collection, CollectionKind
from models.collection_film import CollectionFilm
from models.film import Film
from models.user import User
from models.user_card import UserCard
from models.user_collection_progress import UserCollectionProgress
from services.cards.create_user_card import CreateUserCardInput, CreateUserCardService
from services.cards.delete_user_card import DeleteUserCardService
from services.collections.refresh_user_collection_progress import (
    RefreshUserCollectionProgressService,
)
from tests.support.user_card_category import ensure_default_category


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'colprog-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int, title: str = 'Collection Film') -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2022,
            poster_url='https://example.com/p.jpg',
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
) -> Collection:
    session_factory = get_session_factory()
    async with session_factory() as session:
        collection = Collection(
            slug=slug,
            kind=CollectionKind.evergreen,
            title='Test Collection',
            film_count=len(film_ids),
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


def _card_payload(*, film_id: int, kinopoisk_id: int) -> CreateUserCardInput:
    return CreateUserCardInput(
        rating=8.0,
        company=CardCompany.alone,
        mood_before=CardMoodBefore.relax,
        mood_after=CardMoodAfter.enjoyed,
        custom_tags=[],
        watch_note='',
        film_id=film_id,
        kinopoisk_id=kinopoisk_id,
        genres=['драма'],
    )


async def _get_progress(user_id: UUID, collection_id: int) -> UserCollectionProgress | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        return (
            await session.execute(
                select(UserCollectionProgress).where(
                    UserCollectionProgress.user_id == user_id,
                    UserCollectionProgress.collection_id == collection_id,
                )
            )
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_refresh_user_collection_progress_counts_rated_films(
    async_client: AsyncClient,
) -> None:
    user = await _create_user(telegram_user_id=901001)
    film_a = await _create_film(kinopoisk_id=901001, title='Film A')
    film_b = await _create_film(kinopoisk_id=901002, title='Film B')
    collection = await _create_collection_with_films(
        slug='test-col-901001',
        film_ids=[film_a.id, film_b.id],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        progress = await RefreshUserCollectionProgressService.build(session).execute(
            user.id,
            collection.id,
        )

    assert progress.rated_count == 0
    assert progress.total_count == 2
    assert progress.completed_at is None

    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        await CreateUserCardService(session).execute(
            user.id,
            _card_payload(film_id=film_a.id, kinopoisk_id=film_a.kinopoisk_id),
        )

    progress = await _get_progress(user.id, collection.id)
    assert progress is not None
    assert progress.rated_count == 1
    assert progress.total_count == 2
    assert progress.completed_at is None


@pytest.mark.asyncio
async def test_create_card_marks_collection_completed(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=901002)
    film = await _create_film(kinopoisk_id=901003, title='Solo Film')
    collection = await _create_collection_with_films(
        slug='test-col-901002',
        film_ids=[film.id],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        await CreateUserCardService(session).execute(
            user.id,
            _card_payload(film_id=film.id, kinopoisk_id=film.kinopoisk_id),
        )

    progress = await _get_progress(user.id, collection.id)
    assert progress is not None
    assert progress.rated_count == 1
    assert progress.total_count == 1
    assert progress.completed_at is not None


@pytest.mark.asyncio
async def test_delete_card_keeps_completed_at_sticky(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=901003)
    film = await _create_film(kinopoisk_id=901004, title='Sticky Film')
    collection = await _create_collection_with_films(
        slug='test-col-901003',
        film_ids=[film.id],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        card = await CreateUserCardService(session).execute(
            user.id,
            _card_payload(film_id=film.id, kinopoisk_id=film.kinopoisk_id),
        )

    progress_before = await _get_progress(user.id, collection.id)
    assert progress_before is not None
    assert progress_before.completed_at is not None
    completed_at = progress_before.completed_at

    async with session_factory() as session:
        await DeleteUserCardService(session).execute(card.id, user.id)

    progress_after = await _get_progress(user.id, collection.id)
    assert progress_after is not None
    assert progress_after.rated_count == 0
    assert progress_after.total_count == 1
    assert progress_after.completed_at == completed_at


@pytest.mark.asyncio
async def test_planned_card_does_not_count_toward_progress(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=901004)
    film = await _create_film(kinopoisk_id=901005, title='Planned Film')
    collection = await _create_collection_with_films(
        slug='test-col-901004',
        film_ids=[film.id],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        category_id = await ensure_default_category(session, user.id)
        planned = UserCard(
            user_id=user.id,
            film_id=film.id,
            category_id=category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=0.0,
            company=CardCompany.alone.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
            is_planned=True,
            display_title=film.title,
        )
        session.add(planned)
        await session.commit()

    async with session_factory() as session:
        progress = await RefreshUserCollectionProgressService.build(session).execute(
            user.id,
            collection.id,
        )

    assert progress.rated_count == 0
    assert progress.completed_at is None
