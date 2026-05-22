from __future__ import annotations

import pytest

from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.search.search_my_user_cards_by_title import SearchMyUserCardsByTitleService
from tests.support.user_card_category import ensure_default_category


@pytest.mark.asyncio
async def test_execute_matches_display_title_manual_card(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=882_011,
            profile_slug='search-card-owner',
            username='sco',
            first_name='S',
            last_name='Co',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code='ru',
        )
        session.add(user)
        await session.flush()
        cat_id = await ensure_default_category(session, user.id)
        session.add(
            UserCard(
                user_id=user.id,
                film_id=None,
                catalog_item_id=None,
                category_id=cat_id,
                provider=CatalogProvider.no_provider,
                external_id=None,
                display_title='ManualOnlyTitleQwerty',
                rating=9.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
            ),
        )
        await session.commit()
        viewer_id = user.id

    async with session_factory() as session:
        hits = await SearchMyUserCardsByTitleService.build(session).execute(viewer_id, 'OnlyTi', limit=15)
        assert len(hits) == 1
        assert hits[0].film_id is None
        assert hits[0].title == 'ManualOnlyTitleQwerty'


@pytest.mark.asyncio
async def test_execute_prefers_joined_film_title_for_match(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=882_012,
            profile_slug='search-card-owner-2',
            username='sco2',
            first_name='S',
            last_name='C2',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code='ru',
        )
        session.add(user)
        await session.flush()
        film = Film(
            kinopoisk_id=882_999,
            title='FilmBackedSearchToken',
            year=2019,
            poster_url='https://example.com/x.jpg',
            genres=['thriller'],
        )
        session.add(film)
        await session.flush()
        cat_id = await ensure_default_category(session, user.id)
        session.add(
            UserCard(
                user_id=user.id,
                film_id=film.id,
                category_id=cat_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                rating=7.0,
                company='friends',
                mood_before='relax',
                mood_after='enjoyed',
            ),
        )
        await session.commit()
        viewer_id = user.id
        expected_film_pk = film.id
        expected_kp = film.kinopoisk_id

    async with session_factory() as session:
        hits = await SearchMyUserCardsByTitleService.build(session).execute(viewer_id, 'SearchTok', limit=15)
        assert len(hits) == 1
        assert hits[0].film_id == expected_film_pk
        assert hits[0].kinopoisk_id == expected_kp
        assert hits[0].film_genres == ['thriller']
        assert hits[0].title == 'FilmBackedSearchToken'


@pytest.mark.asyncio
async def test_execute_does_not_return_other_users_cards(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        a = User(
            telegram_user_id=882_013,
            profile_slug='a-search',
            username='sa',
            first_name='A',
            last_name='A',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code='ru',
        )
        b = User(
            telegram_user_id=882_014,
            profile_slug='b-search',
            username='sb',
            first_name='B',
            last_name='B',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code='ru',
        )
        session.add_all((a, b))
        await session.flush()
        cat_a = await ensure_default_category(session, a.id)
        cat_b = await ensure_default_category(session, b.id)
        session.add(
            UserCard(
                user_id=a.id,
                film_id=None,
                catalog_item_id=None,
                category_id=cat_a,
                provider=CatalogProvider.no_provider,
                external_id=None,
                display_title='AlicePrivateTokenZZ',
                rating=8.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
            ),
        )
        session.add(
            UserCard(
                user_id=b.id,
                film_id=None,
                catalog_item_id=None,
                category_id=cat_b,
                provider=CatalogProvider.no_provider,
                external_id=None,
                display_title='AlicePrivateTokenZZ',
                rating=8.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
            ),
        )
        await session.commit()

    async with session_factory() as session:
        visible = await SearchMyUserCardsByTitleService.build(session).execute(a.id, 'PrivateTok', limit=15)
        assert len(visible) == 1
        assert visible[0].title == 'AlicePrivateTokenZZ'
