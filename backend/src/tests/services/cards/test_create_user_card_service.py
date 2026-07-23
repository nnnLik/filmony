"""Direct service coverage for create_user_card validation and branches."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.cards.create_user_card import (
    CatalogItemNotFoundError,
    CreateUserCardInput,
    CreateUserCardService,
    FilmNotFoundError,
    UserCardAlreadyExistsError,
    UserCardValidationError,
    _normalize_genres,
    _normalize_rating,
    _normalize_tags,
    _normalize_catalog_external_id,
    _normalize_display_summary,
    _normalize_optional_url,
    _validate_create_subject_modes,
)
from tests.support.user_card_category import ensure_default_category


def test_normalize_rating_rejects_non_finite_and_bad_step() -> None:
    with pytest.raises(UserCardValidationError, match='finite'):
        _normalize_rating(float('nan'))
    with pytest.raises(UserCardValidationError, match='0.5 step'):
        _normalize_rating(7.3)
    with pytest.raises(UserCardValidationError, match='\\[1, 10\\]'):
        _normalize_rating(10.5)


def test_normalize_tags_dedupes_and_limits() -> None:
    assert _normalize_tags([' A ', 'a', 'B']) == ['A', 'B']
    with pytest.raises(UserCardValidationError, match='max length'):
        _normalize_tags(['x' * 41])
    with pytest.raises(UserCardValidationError, match='max 5'):
        _normalize_tags(['a', 'b', 'c', 'd', 'e', 'f'])


def test_normalize_genres_limits() -> None:
    with pytest.raises(UserCardValidationError, match='max length'):
        _normalize_genres(['x' * 81])
    with pytest.raises(UserCardValidationError, match='max 20'):
        _normalize_genres([f'g{i}' for i in range(21)])


def test_normalize_catalog_external_id_and_urls() -> None:
    assert _normalize_catalog_external_id('  abc  ') == 'abc'
    assert _normalize_catalog_external_id('') is None
    with pytest.raises(UserCardValidationError, match='external_id max length'):
        _normalize_catalog_external_id('x' * 256)
    assert _normalize_display_summary('  hello  ') == 'hello'
    with pytest.raises(UserCardValidationError, match='display_summary max length'):
        _normalize_display_summary('x' * 8001)
    with pytest.raises(UserCardValidationError, match='display_cover_url max length'):
        _normalize_optional_url('x' * 2049, field='display_cover_url')


def test_validate_create_subject_modes_branches() -> None:
    base = CreateUserCardInput(
        rating=8.0,
        company=CardCompany.alone,
        mood_before=CardMoodBefore.relax,
        mood_after=CardMoodAfter.enjoyed,
        custom_tags=[],
        watch_note='',
    )
    with pytest.raises(UserCardValidationError, match='display_title is required for no_provider'):
        _validate_create_subject_modes(
            replace(base, provider=CatalogProvider.no_provider),
            None,
            has_film=False,
            has_catalog=False,
            manual_title='',
        )
    with pytest.raises(UserCardValidationError, match='external_id is required for youtube'):
        _validate_create_subject_modes(
            replace(base, provider=CatalogProvider.youtube),
            None,
            has_film=False,
            has_catalog=False,
            manual_title='Video',
        )
    with pytest.raises(UserCardValidationError, match='cannot be combined with film_id'):
        _validate_create_subject_modes(
            replace(
                base,
                provider=CatalogProvider.youtube,
                external_id='abc12345678',
                display_title='Video',
            ),
            'abc12345678',
            has_film=True,
            has_catalog=False,
            manual_title='Video',
        )
    with pytest.raises(UserCardValidationError, match='provider is required when external_id'):
        _validate_create_subject_modes(
            replace(base, external_id='123'),
            '123',
            has_film=False,
            has_catalog=False,
            manual_title='',
        )


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'cuc-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Create Card Film',
            year=2022,
            poster_url='https://example.com/p.jpg',
            genres=['комедия'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


def _base_payload(**overrides: object) -> CreateUserCardInput:
    defaults = {
        'rating': 7.5,
        'company': CardCompany.alone,
        'mood_before': CardMoodBefore.relax,
        'mood_after': CardMoodAfter.enjoyed,
        'custom_tags': [],
        'watch_note': '',
    }
    defaults.update(overrides)
    return CreateUserCardInput(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_create_film_backed_missing_kinopoisk_id(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892001)
    film = await _create_film(kinopoisk_id=892001)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError, match='kinopoisk_id is required'):
            await svc.execute(
                user.id,
                _base_payload(film_id=film.id, kinopoisk_id=None, genres=film.genres or []),
            )


@pytest.mark.asyncio
async def test_create_film_backed_film_not_found(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892002)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(FilmNotFoundError):
            await svc.execute(
                user.id,
                _base_payload(film_id=999999, kinopoisk_id=1, genres=[]),
            )


@pytest.mark.asyncio
async def test_create_film_backed_kinopoisk_mismatch(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892003)
    film = await _create_film(kinopoisk_id=892003)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError, match='does not match'):
            await svc.execute(
                user.id,
                _base_payload(
                    film_id=film.id,
                    kinopoisk_id=film.kinopoisk_id + 1,
                    genres=film.genres or [],
                ),
            )


@pytest.mark.asyncio
async def test_create_catalog_backed_not_found(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892004)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(CatalogItemNotFoundError):
            await svc.execute(
                user.id,
                _base_payload(catalog_item_id=999999, display_title='Game'),
            )


@pytest.mark.asyncio
async def test_create_catalog_without_film_requires_title(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892005)
    session_factory = get_session_factory()
    async with session_factory() as session:
        game_ci = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id='8920051',
            film_id=None,
        )
        session.add(game_ci)
        await session.commit()
        await session.refresh(game_ci)
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError, match='display_title is required'):
            await svc.execute(
                user.id,
                _base_payload(catalog_item_id=game_ci.id, display_title=''),
            )


@pytest.mark.asyncio
async def test_create_youtube_card_success(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892006)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(
                provider=CatalogProvider.youtube,
                external_id='abc12345678',
                display_title='My Video',
                source_url='https://www.youtube.com/watch?v=abc12345678',
            ),
        )
        assert card.provider == CatalogProvider.youtube
        assert card.external_id == 'abc12345678'


@pytest.mark.asyncio
async def test_create_youtube_card_duplicate_raises(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892007)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        payload = _base_payload(
            provider=CatalogProvider.youtube,
            external_id='dup12345678',
            display_title='Duplicate Video',
        )
        await svc.execute(user.id, payload)
        with pytest.raises(UserCardAlreadyExistsError):
            await svc.execute(user.id, payload)


@pytest.mark.asyncio
async def test_create_manual_title_too_long(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892008)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError, match='display_title max length'):
            await svc.execute(
                user.id,
                _base_payload(display_title='x' * 256),
            )


@pytest.mark.asyncio
async def test_create_watch_note_spoiler_validation(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892009)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError):
            await svc.execute(
                user.id,
                _base_payload(display_title='Spoiler card', watch_note='⟦/S⟧'),
            )


@pytest.mark.asyncio
async def test_create_via_kinopoisk_external_bridges_catalog(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892011)
    film = await _create_film(kinopoisk_id=892011)
    session_factory = get_session_factory()
    async with session_factory() as session:
        ci = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(ci)
        await session.commit()
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                genres=film.genres or [],
            ),
        )
        assert card.catalog_item_id == ci.id
        assert card.film_id == film.id


@pytest.mark.asyncio
async def test_create_film_backed_upgrades_planned_card(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892012)
    film = await _create_film(kinopoisk_id=892012)
    session_factory = get_session_factory()
    async with session_factory() as session:
        category_id = await ensure_default_category(session, user.id)
        planned = UserCard(
            user_id=user.id,
            category_id=category_id,
            film_id=film.id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            is_planned=True,
            display_title=film.title,
            rating=0,
            company=CardCompany.alone.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
        )
        session.add(planned)
        await session.commit()
        svc = CreateUserCardService(session)
        upgraded = await svc.execute(
            user.id,
            _base_payload(
                film_id=film.id,
                kinopoisk_id=film.kinopoisk_id,
                genres=film.genres or [],
            ),
        )
        assert upgraded.id == planned.id
        assert upgraded.is_planned is False


@pytest.mark.asyncio
async def test_create_catalog_backed_with_film(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892013)
    film = await _create_film(kinopoisk_id=892013)
    session_factory = get_session_factory()
    async with session_factory() as session:
        ci = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(catalog_item_id=ci.id, genres=['комедия']),
        )
        assert card.film_id == film.id
        assert card.display_title == film.title


@pytest.mark.asyncio
async def test_create_manual_new_entity(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892014)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(
                display_title='Brand New Manual',
                custom_tags=['tag1'],
            ),
        )
        assert card.display_title == 'Brand New Manual'
        assert card.is_planned is False


@pytest.mark.asyncio
async def test_create_youtube_title_too_long(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892015)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        with pytest.raises(UserCardValidationError, match='display_title max length'):
            await svc.execute(
                user.id,
                _base_payload(
                    provider=CatalogProvider.youtube,
                    external_id='longtitle01',
                    display_title='x' * 256,
                ),
            )


@pytest.mark.asyncio
async def test_create_upgrades_planned_manual_card(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892010)
    title = 'Planned Manual Show'
    session_factory = get_session_factory()
    async with session_factory() as session:
        category_id = await ensure_default_category(session, user.id)
        planned = UserCard(
            user_id=user.id,
            category_id=category_id,
            provider=CatalogProvider.no_provider,
            is_planned=True,
            display_title=title,
            rating=0,
            company=CardCompany.alone.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
        )
        session.add(planned)
        await session.commit()
        svc = CreateUserCardService(session)
        upgraded = await svc.execute(
            user.id,
            _base_payload(display_title=title, rating=9.0),
        )
        assert upgraded.id == planned.id
        assert upgraded.is_planned is False
        assert upgraded.rating == 9.0


@pytest.mark.asyncio
async def test_create_catalog_backed_upgrades_planned_card(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892016)
    film = await _create_film(kinopoisk_id=892016)
    session_factory = get_session_factory()
    async with session_factory() as session:
        ci = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        category_id = await ensure_default_category(session, user.id)
        planned = UserCard(
            user_id=user.id,
            category_id=category_id,
            catalog_item_id=ci.id,
            film_id=film.id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            is_planned=True,
            display_title=film.title,
            rating=0,
            company=CardCompany.alone.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
        )
        session.add(planned)
        await session.commit()
        svc = CreateUserCardService(session)
        upgraded = await svc.execute(
            user.id,
            _base_payload(catalog_item_id=ci.id, genres=film.genres or []),
        )
        assert upgraded.id == planned.id
        assert upgraded.is_planned is False


@pytest.mark.asyncio
async def test_create_film_backed_duplicate_raises(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892017)
    film = await _create_film(kinopoisk_id=892017)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        payload = _base_payload(
            film_id=film.id,
            kinopoisk_id=film.kinopoisk_id,
            genres=film.genres or [],
        )
        await svc.execute(user.id, payload)
        with pytest.raises(UserCardAlreadyExistsError):
            await svc.execute(user.id, payload)


@pytest.mark.asyncio
async def test_create_catalog_game_item_with_display_title(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892018)
    session_factory = get_session_factory()
    async with session_factory() as session:
        ci = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id='8920181',
            film_id=None,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(
                catalog_item_id=ci.id,
                display_title='Indie Game',
                display_cover_url='https://example.com/cover.jpg',
                display_summary='Summary text',
            ),
        )
        assert card.display_title == 'Indie Game'
        assert card.display_cover_url == 'https://example.com/cover.jpg'


@pytest.mark.asyncio
async def test_create_youtube_card_with_custom_tags(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=892019)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user.id)
        svc = CreateUserCardService(session)
        card = await svc.execute(
            user.id,
            _base_payload(
                provider=CatalogProvider.youtube,
                external_id='tagged12345',
                display_title='Tagged Video',
                custom_tags=['review', 'classic'],
            ),
        )
        assert card.external_id == 'tagged12345'
