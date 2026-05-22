from __future__ import annotations

from uuid import uuid4

import pytest

from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.search.search_catalog_cards import SearchCatalogCardsService
from tests.support.user_card_category import ensure_default_category


@pytest.mark.asyncio
async def test_search_catalog_cards_service_matches_film_and_manual_titles(prepare_db: None) -> None:
    session_factory = get_session_factory()
    owner_a_id = uuid4()
    owner_b_id = uuid4()

    async with session_factory() as session:
        owner_a = User(
            id=owner_a_id,
            telegram_user_id=81001,
            profile_slug='search-owner-a',
            username='search_owner_a',
            first_name='Search',
            last_name='OwnerA',
            photo_url=None,
            display_name='Search Owner A',
            bio=None,
            language_code='ru',
        )
        owner_b = User(
            id=owner_b_id,
            telegram_user_id=81002,
            profile_slug='search-owner-b',
            username='search_owner_b',
            first_name='Search',
            last_name='OwnerB',
            photo_url=None,
            display_name='Search Owner B',
            bio=None,
            language_code='ru',
        )
        session.add_all([owner_a, owner_b])
        await session.flush()

        film = Film(
            kinopoisk_id=920001,
            title='Найди меня карточка',
            year=2022,
            poster_url='https://example.com/film.jpg',
            genres=['драма'],
            short_description='Короткое описание фильма',
            description='Полное описание фильма',
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
            display_title='Найди меня карточка',
            display_cover_url='https://example.com/manual.jpg',
            display_summary='Ручное описание карточки',
            rating=8.0,
            company='friends',
            mood_before='laugh',
            mood_after='enjoyed',
        )
        session.add_all([film_card, manual_card])
        await session.commit()
        film_card_id = film_card.id
        manual_card_id = manual_card.id

    async with session_factory() as session:
        svc = SearchCatalogCardsService.build(session)
        result = await svc.execute('Найди меня карточка', 20)

    ids = {hit.card_id for hit in result}
    assert {film_card_id, manual_card_id}.issubset(ids)
    film_hit = next(hit for hit in result if hit.card_id == film_card_id)
    manual_hit = next(hit for hit in result if hit.card_id == manual_card_id)

    assert film_hit.title == 'Найди меня карточка'
    assert film_hit.year == 2022
    assert film_hit.poster_url == 'https://example.com/film.jpg'
    assert film_hit.summary == 'Короткое описание фильма'
    assert film_hit.author_profile_slug == 'search-owner-a'

    assert manual_hit.title == 'Найди меня карточка'
    assert manual_hit.year is None
    assert manual_hit.poster_url == 'https://example.com/manual.jpg'
    assert manual_hit.summary == 'Ручное описание карточки'
    assert manual_hit.author_profile_slug == 'search-owner-b'
