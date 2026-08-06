"""Integration tests for collection-completion achievement unlock and sticky behavior."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.achievement import Achievement
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogProvider
from models.collection import Collection, CollectionKind
from models.collection_film import CollectionFilm
from models.film import Film
from models.user import User
from models.user_achievement import UserAchievement
from models.user_card import UserCard
from services.achievements.grant_collection_achievement import GrantCollectionAchievementService
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
            profile_slug=f'ach-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int, title: str = 'Achievement Film') -> Film:
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


async def _create_collection_with_films(*, slug: str, film_ids: list[int]) -> Collection:
    session_factory = get_session_factory()
    async with session_factory() as session:
        collection = Collection(
            slug=slug,
            kind=CollectionKind.evergreen,
            title=f'Achievement {slug}',
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


async def _create_achievement(*, collection: Collection) -> Achievement:
    session_factory = get_session_factory()
    async with session_factory() as session:
        achievement = Achievement(
            slug=collection.slug,
            collection_slug=collection.slug,
            title=collection.title,
            description='Complete the collection',
        )
        session.add(achievement)
        await session.commit()
        await session.refresh(achievement)
        return achievement


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


async def _count_user_achievements(user_id: UUID, achievement_id: int) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        return int(
            (
                await session.execute(
                    select(UserAchievement).where(
                        UserAchievement.user_id == user_id,
                        UserAchievement.achievement_id == achievement_id,
                    )
                )
            )
            .scalars()
            .all()
            .__len__()
        )


@pytest.mark.asyncio
async def test_collection_completion_grants_achievement_once(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910001)
    film = await _create_film(kinopoisk_id=910001)
    collection = await _create_collection_with_films(slug='ach-col-910001', film_ids=[film.id])
    achievement = await _create_achievement(collection=collection)

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        await CreateUserCardService(session).execute(
            user.id,
            _card_payload(film_id=film.id, kinopoisk_id=film.kinopoisk_id),
        )

    assert await _count_user_achievements(user.id, achievement.id) == 1

    async with session_factory() as session:
        await GrantCollectionAchievementService.build(session).execute(user.id, collection.slug)

    assert await _count_user_achievements(user.id, achievement.id) == 1


@pytest.mark.asyncio
async def test_user_achievement_sticky_after_rating_deleted(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910002)
    film = await _create_film(kinopoisk_id=910002)
    collection = await _create_collection_with_films(slug='ach-col-910002', film_ids=[film.id])
    achievement = await _create_achievement(collection=collection)

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        card = await CreateUserCardService(session).execute(
            user.id,
            _card_payload(film_id=film.id, kinopoisk_id=film.kinopoisk_id),
        )

    assert await _count_user_achievements(user.id, achievement.id) == 1

    async with session_factory() as session:
        await DeleteUserCardService(session).execute(card.id, user.id)
        await RefreshUserCollectionProgressService.build(session).execute(user.id, collection.id)

    assert await _count_user_achievements(user.id, achievement.id) == 1


@pytest.mark.asyncio
async def test_recalculate_rarity_uses_meaningful_rated_card_denominator(
    async_client: AsyncClient,
) -> None:
    from services.achievements.recalculate_achievement_rarity import (
        RecalculateAchievementRarityService,
    )

    holder = await _create_user(telegram_user_id=910003)
    eligible_other = await _create_user(telegram_user_id=910004)
    planned_only = await _create_user(telegram_user_id=910005)

    film = await _create_film(kinopoisk_id=910003)
    collection = await _create_collection_with_films(slug='ach-col-910003', film_ids=[film.id])
    achievement = await _create_achievement(collection=collection)

    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, holder.id)
        await CreateUserCardService(session).execute(
            holder.id,
            _card_payload(film_id=film.id, kinopoisk_id=film.kinopoisk_id),
        )

        category_id = await ensure_default_category(session, eligible_other.id)
        other_film = Film(
            kinopoisk_id=910006,
            title='Other',
            year=2020,
            poster_url='https://example.com/o.jpg',
            genres=['драма'],
        )
        session.add(other_film)
        await session.flush()
        session.add(
            UserCard(
                user_id=eligible_other.id,
                film_id=other_film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(other_film.kinopoisk_id),
                rating=7.0,
                company=CardCompany.alone.value,
                mood_before=CardMoodBefore.relax.value,
                mood_after=CardMoodAfter.enjoyed.value,
                watch_note='',
                is_planned=False,
                display_title=other_film.title,
            )
        )

        planned_category = await ensure_default_category(session, planned_only.id)
        session.add(
            UserCard(
                user_id=planned_only.id,
                film_id=other_film.id,
                category_id=planned_category,
                provider=CatalogProvider.kinopoisk,
                external_id='910007',
                rating=0.0,
                company=CardCompany.alone.value,
                mood_before=CardMoodBefore.relax.value,
                mood_after=CardMoodAfter.enjoyed.value,
                watch_note='',
                is_planned=True,
                display_title='Planned',
            )
        )
        await session.commit()

    async with session_factory() as session:
        await RecalculateAchievementRarityService.build(session).execute(
            achievement_id=achievement.id
        )

    async with session_factory() as session:
        refreshed = (
            await session.execute(select(Achievement).where(Achievement.id == achievement.id))
        ).scalar_one()
        assert refreshed.eligible_users_count == 2
        assert refreshed.holders_count == 1
        assert float(refreshed.rarity_percent) == 50.0
