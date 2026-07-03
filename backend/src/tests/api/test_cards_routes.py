from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from celery_app import app as celery_app_instance
from conf import settings
from core.database import get_session_factory
from integrations.telegram.bot_api_client import TelegramBotApiClient, TelegramSendMessageResult
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.reaction_type import ReactionType
from models.user import User
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


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
    short_description: str | None = None,
    description: str | None = None,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
            genres=genres or [],
            short_description=short_description,
            description=description,
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _catalog_item_id_for_film_id(film_id: int) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        existing = (
            await session.execute(select(CatalogItem.id).where(CatalogItem.film_id == film_id))
        ).scalar_one_or_none()
        if existing is not None:
            return int(existing)
        film = (await session.execute(select(Film).where(Film.id == film_id))).scalar_one()
        ci = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        return int(ci.id)


async def _create_rawg_catalog_item_with_game(
    *,
    rawg_numeric_id: int,
    released: str = '2015-05-18',
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        game = Game(rawg_id=rawg_numeric_id, released=released)
        session.add(game)
        await session.commit()
        await session.refresh(game)
        ci = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id=str(rawg_numeric_id),
            game_id=int(game.id),
            film_id=None,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        return int(ci.id)


@pytest.mark.asyncio
async def test_get_rawg_game_card_detail_has_release_fields(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=760050)
    cat_id = await _create_rawg_catalog_item_with_game(rawg_numeric_id=7600501)
    created = await async_client.post(
        '/api/cards',
        json={
            'catalog_item_id': cat_id,
            'display_title': 'The Witcher 3',
            'genres': [],
            'rating': 9.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    cid = int(created.json()['id'])
    detail = await async_client.get(f'/api/cards/{cid}')
    assert detail.status_code == 200
    d = detail.json()
    assert d['film_id'] is None
    assert d['film_year'] is None
    assert d['release_year'] == 2015
    assert d['release_date'] == '2015-05-18'


@pytest.mark.asyncio
async def test_create_card_via_kinopoisk_provider_external_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=761020)
    film = await _create_film(kinopoisk_id=761021)
    ci_id = await _catalog_item_id_for_film_id(film.id)
    r = await async_client.post(
        '/api/cards',
        json={
            'provider': 'kinopoisk',
            'external_id': str(film.kinopoisk_id),
            'genres': film.genres or [],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == str(film.kinopoisk_id)
    assert body['film_id'] == film.id
    assert body['catalog_item_id'] == ci_id


@pytest.mark.asyncio
async def test_create_card_kinopoisk_external_duplicate_returns_409(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=761022)
    film = await _create_film(kinopoisk_id=761023)
    await _catalog_item_id_for_film_id(film.id)
    payload = {
        'provider': 'kinopoisk',
        'external_id': str(film.kinopoisk_id),
        'genres': [],
        'rating': 8.0,
        'company': 'alone',
        'mood_before': 'relax',
        'mood_after': 'enjoyed',
        'custom_tags': [],
    }
    assert (await async_client.post('/api/cards', json=payload)).status_code == 200
    assert (await async_client.post('/api/cards', json=payload)).status_code == 409


@pytest.mark.asyncio
async def test_create_card_kinopoisk_external_unknown_catalog_returns_404(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=761024)
    r = await async_client.post(
        '/api/cards',
        json={
            'provider': 'kinopoisk',
            'external_id': '999888777666',
            'genres': [],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 404


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
    assert body['display_title'] == film.title
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == str(film.kinopoisk_id)


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
async def test_create_manual_movie_card_without_film(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=760010)
    r = await async_client.post(
        '/api/cards',
        json={
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
            'watch_note': '',
            'display_title': '  Кастомный спектакль  ',
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body['film_id'] is None
    assert body['catalog_item_id'] is None
    assert body['display_title'] == 'Кастомный спектакль'
    assert body['provider'] == 'no_provider'
    assert body['external_id'] is None


@pytest.mark.asyncio
async def test_get_manual_movie_card_detail_includes_display_and_legacy_fields(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=760011)
    created = await async_client.post(
        '/api/cards',
        json={
            'rating': 6.0,
            'company': 'partner',
            'mood_before': 'thrill',
            'mood_after': 'tense',
            'custom_tags': [],
            'watch_note': 'note',
            'display_title': 'Manual title',
        },
    )
    assert created.status_code == 200
    cid = int(created.json()['id'])
    detail = await async_client.get(f'/api/cards/{cid}')
    assert detail.status_code == 200
    d = detail.json()
    assert d['display_title'] == 'Manual title'
    assert d['film_title'] == 'Manual title'
    assert d['film_id'] is None
    assert d['catalog_item_id'] is None


@pytest.mark.asyncio
async def test_create_card_by_catalog_item_id_duplicate_returns_409(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=760012)
    film = await _create_film(kinopoisk_id=770012)
    cat_id = await _catalog_item_id_for_film_id(film.id)
    payload = {
        'catalog_item_id': cat_id,
        'genres': list(film.genres or []),
        'rating': 7.0,
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
        cat_id = await ensure_default_category(session, user.id)
        card = UserCard(
            user_id=user.id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
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
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == str(film.kinopoisk_id)
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
async def test_get_planned_card_returns_is_planned_true(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=623)
    film = await _create_film(kinopoisk_id=100623)
    created = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert created.status_code == 201

    planned = await async_client.get(f'/api/me/planned-card?film_id={film.id}')
    assert planned.status_code == 200
    card_id = planned.json()['user_card_id']

    fetched = await async_client.get(f'/api/cards/{card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['is_planned'] is True
    assert body['planned_watch_partners'] == []


@pytest.mark.asyncio
async def test_get_planned_card_includes_watch_partners(async_client: AsyncClient) -> None:
    from models.user_subscription import UserSubscription

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor = User(
            telegram_user_id=624001,
            profile_slug='planned-partners-actor',
            username='planned_actor',
            first_name='Actor',
            last_name=None,
            photo_url=None,
            display_name='Actor',
            bio=None,
            language_code='ru',
        )
        partner = User(
            telegram_user_id=624002,
            profile_slug='planned-partners-friend',
            username='planned_friend',
            first_name='Friend',
            last_name=None,
            photo_url=None,
            display_name='Friend',
            bio=None,
            language_code='ru',
        )
        session.add(actor)
        session.add(partner)
        await session.flush()
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=partner.id))
        session.add(UserSubscription(follower_user_id=partner.id, following_user_id=actor.id))
        film = Film(
            kinopoisk_id=100624,
            title='Partners Film',
            year=2024,
            poster_url=None,
            genres=[],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id='100624',
                film_id=film.id,
            )
        )
        await session.commit()
        partner_id = str(partner.id)
        film_id = film.id

    await _login(async_client, telegram_user_id=624001)
    created = await async_client.post(
        '/api/me/watchlist',
        json={
            'film_id': film_id,
            'company': 'friends',
            'watch_with_user_ids': [partner_id],
        },
    )
    assert created.status_code == 201

    planned = await async_client.get(f'/api/me/planned-card?film_id={film_id}')
    card_id = planned.json()['user_card_id']

    await _login(async_client, telegram_user_id=624002)
    partner_planned = await async_client.get(f'/api/me/planned-card?film_id={film_id}')
    partner_planned_card_id = partner_planned.json()['user_card_id']

    await _login(async_client, telegram_user_id=624001)
    fetched = await async_client.get(f'/api/cards/{card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['is_planned'] is True
    assert len(body['planned_watch_partners']) == 1
    assert body['planned_watch_partners'][0]['id'] == partner_id
    assert body['planned_watch_partners'][0]['display_name'] == 'Friend'
    assert body['planned_watch_partners'][0]['has_rated'] is False
    assert body['planned_watch_partners'][0]['rating'] is None
    assert body['planned_watch_partners'][0]['rated_user_card_id'] is None
    assert body['planned_watch_partners'][0]['planned_user_card_id'] == partner_planned_card_id


@pytest.mark.asyncio
async def test_get_planned_card_partner_watch_status_when_rated(async_client: AsyncClient) -> None:
    from models.user_subscription import UserSubscription
    from models.watchlist_entry import WatchlistEntry
    from tests.support.user_card_category import ensure_default_category

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor = User(
            telegram_user_id=624003,
            profile_slug='planned-partners-rated-actor',
            username='planned_rated_actor',
            first_name='Actor',
            last_name=None,
            photo_url=None,
            display_name='Actor',
            bio=None,
            language_code='ru',
        )
        partner = User(
            telegram_user_id=624004,
            profile_slug='planned-partners-rated-friend',
            username='planned_rated_friend',
            first_name='Friend',
            last_name=None,
            photo_url=None,
            display_name='Friend',
            bio=None,
            language_code='ru',
        )
        session.add(actor)
        session.add(partner)
        await session.flush()
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=partner.id))
        session.add(UserSubscription(follower_user_id=partner.id, following_user_id=actor.id))
        film = Film(
            kinopoisk_id=100627,
            title='Rated Partners Film',
            year=2024,
            poster_url=None,
            genres=[],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id='100627',
                film_id=film.id,
            )
        )
        actor_cat_id = await ensure_default_category(session, actor.id)
        partner_cat_id = await ensure_default_category(session, partner.id)
        actor_planned_card = UserCard(
            user_id=actor.id,
            film_id=film.id,
            category_id=actor_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100627',
            rating=0.0,
            company='friends',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=True,
        )
        partner_rated_card = UserCard(
            user_id=partner.id,
            film_id=film.id,
            category_id=partner_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100627',
            rating=9.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=False,
        )
        session.add(actor_planned_card)
        session.add(partner_rated_card)
        await session.flush()
        session.add(
            WatchlistEntry(
                user_id=actor.id,
                card_id='kp:100627',
                provider_meta={
                    'provider': 'kinopoisk',
                    'data': {
                        'kp_id': film.kinopoisk_id,
                        'title': film.title,
                        'poster_url': film.poster_url,
                    },
                },
                watch_tag='watch_later',
                watch_with_user_id=partner.id,
                watch_with_user_ids=[str(partner.id)],
            )
        )
        await session.commit()
        partner_id = str(partner.id)
        actor_planned_card_id = actor_planned_card.id
        partner_rated_card_id = partner_rated_card.id

    await _login(async_client, telegram_user_id=624003)
    fetched = await async_client.get(f'/api/cards/{actor_planned_card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['is_planned'] is True
    assert len(body['planned_watch_partners']) == 1
    partner_body = body['planned_watch_partners'][0]
    assert partner_body['id'] == partner_id
    assert partner_body['has_rated'] is True
    assert partner_body['rating'] == 9.0
    assert partner_body['rated_user_card_id'] == partner_rated_card_id
    assert partner_body['planned_user_card_id'] is None


@pytest.mark.asyncio
async def test_get_planned_card_partner_only_planned_card_not_rated(
    async_client: AsyncClient,
) -> None:
    from models.user_subscription import UserSubscription
    from models.watchlist_entry import WatchlistEntry
    from tests.support.user_card_category import ensure_default_category

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor = User(
            telegram_user_id=624005,
            profile_slug='planned-only-partner-act',
            username='planned_only_actor',
            first_name='Actor',
            last_name=None,
            photo_url=None,
            display_name='Actor',
            bio=None,
            language_code='ru',
        )
        partner = User(
            telegram_user_id=624006,
            profile_slug='planned-only-partner-fr',
            username='planned_only_friend',
            first_name='Friend',
            last_name=None,
            photo_url=None,
            display_name='Friend',
            bio=None,
            language_code='ru',
        )
        session.add(actor)
        session.add(partner)
        await session.flush()
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=partner.id))
        session.add(UserSubscription(follower_user_id=partner.id, following_user_id=actor.id))
        film = Film(
            kinopoisk_id=100628,
            title='Planned Only Partners Film',
            year=2024,
            poster_url=None,
            genres=[],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id='100628',
                film_id=film.id,
            )
        )
        actor_cat_id = await ensure_default_category(session, actor.id)
        partner_cat_id = await ensure_default_category(session, partner.id)
        actor_planned_card = UserCard(
            user_id=actor.id,
            film_id=film.id,
            category_id=actor_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100628',
            rating=0.0,
            company='friends',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=True,
        )
        partner_planned_card = UserCard(
            user_id=partner.id,
            film_id=film.id,
            category_id=partner_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100628',
            rating=0.0,
            company='friends',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=True,
        )
        session.add(actor_planned_card)
        session.add(partner_planned_card)
        await session.flush()
        session.add(
            WatchlistEntry(
                user_id=actor.id,
                card_id='kp:100628',
                provider_meta={
                    'provider': 'kinopoisk',
                    'data': {
                        'kp_id': film.kinopoisk_id,
                        'title': film.title,
                        'poster_url': film.poster_url,
                    },
                },
                watch_tag='watch_later',
                watch_with_user_id=partner.id,
                watch_with_user_ids=[str(partner.id)],
            )
        )
        await session.commit()
        partner_id = str(partner.id)
        actor_planned_card_id = actor_planned_card.id
        partner_planned_card_id = partner_planned_card.id

    await _login(async_client, telegram_user_id=624005)
    fetched = await async_client.get(f'/api/cards/{actor_planned_card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['is_planned'] is True
    assert len(body['planned_watch_partners']) == 1
    partner_body = body['planned_watch_partners'][0]
    assert partner_body['id'] == partner_id
    assert partner_body['has_rated'] is False
    assert partner_body['rating'] is None
    assert partner_body['rated_user_card_id'] is None
    assert partner_body['planned_user_card_id'] == partner_planned_card_id


@pytest.mark.asyncio
async def test_get_planned_card_partner_zero_rating_not_rated(
    async_client: AsyncClient,
) -> None:
    from models.user_subscription import UserSubscription
    from models.watchlist_entry import WatchlistEntry
    from tests.support.user_card_category import ensure_default_category

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor = User(
            telegram_user_id=624007,
            profile_slug='planned-zero-rating-act',
            username='zero_rating_actor',
            first_name='Actor',
            last_name=None,
            photo_url=None,
            display_name='Actor',
            bio=None,
            language_code='ru',
        )
        partner = User(
            telegram_user_id=624008,
            profile_slug='planned-zero-rating-fr',
            username='zero_rating_friend',
            first_name='Friend',
            last_name=None,
            photo_url=None,
            display_name='Friend',
            bio=None,
            language_code='ru',
        )
        session.add(actor)
        session.add(partner)
        await session.flush()
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=partner.id))
        session.add(UserSubscription(follower_user_id=partner.id, following_user_id=actor.id))
        film = Film(
            kinopoisk_id=100629,
            title='Zero Rating Partners Film',
            year=2024,
            poster_url=None,
            genres=[],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id='100629',
                film_id=film.id,
            )
        )
        actor_cat_id = await ensure_default_category(session, actor.id)
        partner_cat_id = await ensure_default_category(session, partner.id)
        actor_planned_card = UserCard(
            user_id=actor.id,
            film_id=film.id,
            category_id=actor_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100629',
            rating=0.0,
            company='friends',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=True,
        )
        partner_zero_rating_card = UserCard(
            user_id=partner.id,
            film_id=film.id,
            category_id=partner_cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='100629',
            rating=0.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=False,
        )
        session.add(actor_planned_card)
        session.add(partner_zero_rating_card)
        await session.flush()
        session.add(
            WatchlistEntry(
                user_id=actor.id,
                card_id='kp:100629',
                provider_meta={
                    'provider': 'kinopoisk',
                    'data': {
                        'kp_id': film.kinopoisk_id,
                        'title': film.title,
                        'poster_url': film.poster_url,
                    },
                },
                watch_tag='watch_later',
                watch_with_user_id=partner.id,
                watch_with_user_ids=[str(partner.id)],
            )
        )
        await session.commit()
        partner_id = str(partner.id)
        actor_planned_card_id = actor_planned_card.id

    await _login(async_client, telegram_user_id=624007)
    fetched = await async_client.get(f'/api/cards/{actor_planned_card_id}')
    assert fetched.status_code == 200
    body = fetched.json()
    assert body['is_planned'] is True
    assert len(body['planned_watch_partners']) == 1
    partner_body = body['planned_watch_partners'][0]
    assert partner_body['id'] == partner_id
    assert partner_body['has_rated'] is False
    assert partner_body['rating'] is None
    assert partner_body['rated_user_card_id'] is None
    assert partner_body['planned_user_card_id'] is None


@pytest.mark.asyncio
async def test_get_planned_card_includes_watchlist_entry_id_for_owner(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=624010)
    film = await _create_film(kinopoisk_id=100625)
    created = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert created.status_code == 201
    entry_id = created.json()['entry_id']

    planned = await async_client.get(f'/api/me/planned-card?film_id={film.id}')
    card_id = planned.json()['user_card_id']

    fetched = await async_client.get(f'/api/cards/{card_id}')
    assert fetched.status_code == 200
    assert fetched.json()['watchlist_entry_id'] == entry_id


@pytest.mark.asyncio
async def test_patch_planned_card_rejects_rating(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=624011)
    film = await _create_film(kinopoisk_id=100626)
    created = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert created.status_code == 201

    planned = await async_client.get(f'/api/me/planned-card?film_id={film.id}')
    card_id = planned.json()['user_card_id']

    blocked = await async_client.patch(f'/api/cards/{card_id}', json={'rating': 8.0})
    assert blocked.status_code == 422
    assert 'planned' in blocked.json()['detail']


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
        cat_id = await ensure_default_category(session, user.id)
        card = UserCard(
            user_id=user.id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
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
        cat_id = await ensure_default_category(session, user.id)
        card = UserCard(
            user_id=user.id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
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
async def test_create_movie_card_comment_with_image_url(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=771)
    film = await _create_film(kinopoisk_id=100771, title='Кадр из зала', year=2020)
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
    media_url = f'/api/feed-posts/media/user_media/movie_card_comments/{me["id"]}/shot.webp'

    only_img = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': '', 'image_url': media_url},
    )
    assert only_img.status_code == 200
    only_body = only_img.json()
    assert only_body['text'] == ''
    assert only_body['image_url'] == media_url

    both = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': 'см. кадр', 'image_url': media_url},
    )
    assert both.status_code == 200
    assert both.json()['image_url'] == media_url

    bad_key = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': '', 'image_url': 'https://example.com/x.jpg'},
    )
    assert bad_key.status_code == 422

    empty_both = await async_client.post(f'/api/cards/{card_id}/comments', json={'text': '   '})
    assert empty_both.status_code == 422

    listed = await async_client.get(f'/api/cards/{card_id}/comments')
    assert listed.status_code == 200
    with_img = [it for it in listed.json()['items'] if it.get('image_url')]
    assert len(with_img) == 2


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
    mentions = r.json().get('referenced_mentions') or []
    assert len(mentions) == 1
    assert str(mentions[0]['user_id']) == str(target['id'])
    assert mentions[0]['profile_slug'] == str(slug_target).lower()
    assert isinstance(mentions[0].get('display_label'), str)
    assert len(mentions[0]['display_label']) > 0

    lst = await async_client.get(f'/api/cards/{card_id}/comments')
    assert lst.status_code == 200
    items = lst.json()['items']
    hit = next(x for x in items if x['id'] == r.json()['id'])
    m2 = hit.get('referenced_mentions') or []
    assert len(m2) == 1
    assert str(m2[0]['user_id']) == str(target['id'])
    assert isinstance(m2[0].get('display_label'), str)
    assert len(m2[0]['display_label']) > 0


@pytest.mark.asyncio
async def test_comment_mention_queues_celery(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_movie_card_comment_mentions'],
        'delay',
        mock_delay,
    )

    author = await _login(async_client, telegram_user_id=90240)
    target = await _login(async_client, telegram_user_id=90241)
    slug_target = await _profile_slug_for_telegram(90241)
    await _login(async_client, telegram_user_id=90240)
    await async_client.post(f'/api/users/{target["id"]}/subscriptions')

    film = await _create_film(kinopoisk_id=10090240, title='Mention celery', year=2021)
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
        json={'text': f'hey ⟦@{slug_target}⟧'},
    )
    assert r.status_code == 200
    comment_id = int(r.json()['id'])

    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs['actor_user_id'] == author['id']
    assert kwargs['card_id'] == card_id
    assert kwargs['comment_id'] == comment_id
    listed = orjson.loads(kwargs['recipient_user_ids_json'])
    assert listed == [target['id']]


@pytest.mark.asyncio
async def test_comment_reply_mention_same_parent_no_mention_celery(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    reply_delay = MagicMock()
    mention_delay = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_comment_reply'],
        'delay',
        reply_delay,
    )
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_movie_card_comment_mentions'],
        'delay',
        mention_delay,
    )

    await _login(async_client, telegram_user_id=90250)
    film = await _create_film(kinopoisk_id=10090250, title='Dedupe reply', year=2020)
    card = await async_client.post(
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
    assert card.status_code == 200
    card_id = card.json()['id']

    author_a = await _login(async_client, telegram_user_id=90251)
    root = await async_client.post(f'/api/cards/{card_id}/comments', json={'text': 'root by A'})
    assert root.status_code == 200
    root_id = int(root.json()['id'])
    slug_a = await _profile_slug_for_telegram(90251)

    await _login(async_client, telegram_user_id=90252)
    await async_client.post(f'/api/users/{author_a["id"]}/subscriptions')

    rep = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={
            'text': f'⟦@{slug_a}⟧ ответ',
            'parent_comment_id': root_id,
        },
    )
    assert rep.status_code == 200

    reply_delay.assert_called_once()
    mention_delay.assert_not_called()


@pytest.mark.asyncio
async def test_comment_root_mention_card_owner_no_mention_celery(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    root_delay = MagicMock()
    mention_delay = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_movie_card_root_comment'],
        'delay',
        root_delay,
    )
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_movie_card_comment_mentions'],
        'delay',
        mention_delay,
    )

    owner = await _login(async_client, telegram_user_id=90260)
    film = await _create_film(kinopoisk_id=10090260, title='Dedupe root', year=2019)
    card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': ['драма'],
            'rating': 7.5,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert card.status_code == 200
    card_id = card.json()['id']
    slug_owner = await _profile_slug_for_telegram(90260)

    await _login(async_client, telegram_user_id=90261)
    await async_client.post(f'/api/users/{owner["id"]}/subscriptions')

    r = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': f'привет ⟦@{slug_owner}⟧'},
    )
    assert r.status_code == 200

    root_delay.assert_called_once()
    mention_delay.assert_not_called()


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
            short_description='Коротко.',
            description='Длинное описание фильма.',
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
    assert body['short_description'] == 'Коротко.'
    assert body['description'] == 'Длинное описание фильма.'

    fetched = await async_client.get(f'/api/films/{body["id"]}')
    assert fetched.status_code == 200
    assert fetched.json()['id'] == body['id']
    assert fetched.json()['genres'] == ['фантастика', 'боевик']
    assert fetched.json()['short_description'] == 'Коротко.'
    assert fetched.json()['description'] == 'Длинное описание фильма.'

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
async def test_get_card_includes_film_synopsis(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=631)
    film = await _create_film(
        kinopoisk_id=100631,
        short_description='Кратко про фильм.',
        description='Развёрнутое описание для теста.',
    )
    created = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': film.genres,
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert created.status_code == 200
    card_id = created.json()['id']
    detail = await async_client.get(f'/api/cards/{card_id}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['film_short_description'] == 'Кратко про фильм.'
    assert body['film_description'] == 'Развёрнутое описание для теста.'


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
            short_description=None,
            description=None,
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
async def test_card_model_uses_partial_unique_indexes_for_film_and_catalog() -> None:
    constraint_names = {c.name for c in UserCard.__table__.constraints}
    assert 'uq_movie_card_user_film' not in constraint_names
    index_names = {ix.name for ix in UserCard.__table__.indexes}
    assert 'uq_user_card_user_film_id_partial' in index_names
    assert 'uq_user_card_user_catalog_item_id_partial' in index_names
    assert 'uq_user_card_user_provider_external_kinopoisk_partial' in index_names


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


@pytest.mark.asyncio
async def test_movie_card_feed_promotes_converted_planned_card(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=918)
    author_a = await _login(async_client, telegram_user_id=9180)
    author_b = await _login(async_client, telegram_user_id=9181)
    await _login(async_client, telegram_user_id=918)
    await async_client.post(f'/api/users/{author_a["id"]}/subscriptions')
    await async_client.post(f'/api/users/{author_b["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=9180)
    planned_film = await _create_film(kinopoisk_id=1009181, title='Planned first')
    planned_watchlist = await async_client.post(
        '/api/me/watchlist', json={'film_id': planned_film.id}
    )
    assert planned_watchlist.status_code == 201

    await _login(async_client, telegram_user_id=9181)
    newer_film = await _create_film(kinopoisk_id=1009182, title='Newer card')
    newer_card = await async_client.post(
        '/api/cards',
        json={
            'film_id': newer_film.id,
            'kinopoisk_id': newer_film.kinopoisk_id,
            'genres': [],
            'rating': 8.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert newer_card.status_code == 200
    newer_card_id = newer_card.json()['id']

    await _login(async_client, telegram_user_id=9180)
    upgraded = await async_client.post(
        '/api/cards',
        json={
            'film_id': planned_film.id,
            'kinopoisk_id': planned_film.kinopoisk_id,
            'genres': [],
            'rating': 9.0,
            'company': 'friends',
            'mood_before': 'laugh',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert upgraded.status_code == 200
    upgraded_card_id = upgraded.json()['id']

    await _login(async_client, telegram_user_id=918)
    feed = await async_client.get('/api/cards/feed?limit=10&mode=subscriptions_only')
    assert feed.status_code == 200
    items = feed.json()['items']
    feed_ids = [item['id'] for item in items]
    assert feed_ids[:2] == [upgraded_card_id, newer_card_id]


@pytest.mark.asyncio
async def test_list_my_card_categories_includes_default_films(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8801)
    r = await async_client.get('/api/me/card-categories')
    assert r.status_code == 200
    items = r.json()['items']
    assert any(it['name'] == 'Фильмы' for it in items)


@pytest.mark.asyncio
async def test_create_my_card_category_and_use_on_card(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8802)
    create_cat = await async_client.post('/api/me/card-categories', json={'name': '  Аниме  '})
    assert create_cat.status_code == 200
    cat_body = create_cat.json()
    assert cat_body['name'] == 'Аниме'

    film = await _create_film(kinopoisk_id=880_002)
    card_r = await async_client.post(
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
            'category_id': cat_body['id'],
        },
    )
    assert card_r.status_code == 200
    out = card_r.json()
    assert out['category']['id'] == cat_body['id']
    assert out['category']['name'] == 'Аниме'

    detail = await async_client.get(f'/api/cards/{out["id"]}')
    assert detail.status_code == 200
    assert detail.json()['category']['name'] == 'Аниме'


@pytest.mark.asyncio
async def test_create_card_without_category_uses_default_films(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8803)
    film = await _create_film(kinopoisk_id=880_003)
    card_r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert card_r.status_code == 200
    assert card_r.json()['category']['name'] == 'Фильмы'


@pytest.mark.asyncio
async def test_patch_card_rejects_other_users_category_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8804)
    await _login(async_client, telegram_user_id=8805)

    create_other_cat = await async_client.post('/api/me/card-categories', json={'name': 'Games'})
    assert create_other_cat.status_code == 200
    foreign_cat_id = create_other_cat.json()['id']

    await _login(async_client, telegram_user_id=8804)
    film = await _create_film(kinopoisk_id=880_004)
    card_r = await async_client.post(
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
    assert card_r.status_code == 200
    card_id = card_r.json()['id']

    patch_bad = await async_client.patch(
        f'/api/cards/{card_id}',
        json={'category_id': foreign_cat_id},
    )
    assert patch_bad.status_code == 422


@pytest.mark.asyncio
async def test_create_card_queues_follower_publish_notify(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    task = celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_user_card']
    monkeypatch.setattr(task, 'delay', mock_delay)

    author = await _login(async_client, telegram_user_id=762)
    follower = await _login(async_client, telegram_user_id=763)
    await _login(async_client, telegram_user_id=763)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=762)
    film = await _create_film(kinopoisk_id=762_001)
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
    cid = int(r.json()['id'])

    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs['actor_user_id'] == author['id']
    assert kwargs['card_id'] == cid
    listed = orjson.loads(kwargs['recipient_user_ids_json'])
    assert listed == [str(follower['id'])]


@pytest.mark.asyncio
async def test_create_card_no_followers_skips_follower_notify(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    task = celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_user_card']
    monkeypatch.setattr(task, 'delay', mock_delay)

    await _login(async_client, telegram_user_id=770)
    film = await _create_film(kinopoisk_id=770_001)
    r = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 7.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert r.status_code == 200
    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_user_card_media_unsafe_key(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/cards/media/user_media/feed_posts/x/x.mp3')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_upload_card_audio_success(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    from services.cards import attach_user_card_audio as attach_audio_mod

    async def fake_upload_execute(
        self: object,
        *,
        user_id,
        content_type,
        data: bytes,
    ) -> str:
        return '/api/cards/media/user_media/movie_card_audio/fake-user/fakefile.mp3'

    monkeypatch.setattr(attach_audio_mod.UploadUserCardAudioService, 'execute', fake_upload_execute)

    await _login(async_client, telegram_user_id=880001)
    film = await _create_film(kinopoisk_id=8800011)
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
    card_id = int(created.json()['id'])
    up = await async_client.post(
        f'/api/cards/{card_id}/audio',
        files={'file': ('x.mp3', b'id3fake', 'audio/mpeg')},
    )
    assert up.status_code == 200
    assert up.json()['url'].endswith('fakefile.mp3')
    detail = await async_client.get(f'/api/cards/{card_id}')
    assert detail.status_code == 200
    body = detail.json()
    assert body['audio_url'].endswith('fakefile.mp3')


@pytest.mark.asyncio
async def test_upload_card_audio_rejects_bad_type(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=880002)
    film = await _create_film(kinopoisk_id=8800022)
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
    card_id = int(created.json()['id'])
    up = await async_client.post(
        f'/api/cards/{card_id}/audio',
        files={'file': ('x.bin', b'hello', 'application/octet-stream')},
    )
    assert up.status_code == 400


@pytest.mark.asyncio
async def test_upload_card_audio_forbidden_other_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=880003)
    film = await _create_film(kinopoisk_id=8800033)
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
    card_id = int(created.json()['id'])
    await _login(async_client, telegram_user_id=880004)
    up = await async_client.post(
        f'/api/cards/{card_id}/audio',
        files={'file': ('x.mp3', b'id3', 'audio/mpeg')},
    )
    assert up.status_code == 403


@pytest.mark.asyncio
async def test_delete_card_audio_success(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    from services.cards import attach_user_card_audio as attach_audio_mod

    async def fake_upload_execute(
        self: object,
        *,
        user_id,
        content_type,
        data: bytes,
    ) -> str:
        return '/api/cards/media/user_media/movie_card_audio/fake-user/fake2.mp3'

    monkeypatch.setattr(attach_audio_mod.UploadUserCardAudioService, 'execute', fake_upload_execute)

    await _login(async_client, telegram_user_id=880005)
    film = await _create_film(kinopoisk_id=8800055)
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
    card_id = int(created.json()['id'])
    assert (
        await async_client.post(
            f'/api/cards/{card_id}/audio',
            files={'file': ('x.mp3', b'id3', 'audio/mpeg')},
        )
    ).status_code == 200
    deleted = await async_client.delete(f'/api/cards/{card_id}/audio')
    assert deleted.status_code == 204
    got = await async_client.get(f'/api/cards/{card_id}')
    assert got.json()['audio_url'] is None


@pytest.mark.asyncio
async def test_upload_card_audio_too_large(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    from api.cards import routes as cards_routes_module

    monkeypatch.setattr(cards_routes_module, 'USER_CARD_AUDIO_MAX_BYTES', 4)

    await _login(async_client, telegram_user_id=880007)
    film = await _create_film(kinopoisk_id=8800077)
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
    card_id = int(created.json()['id'])
    up = await async_client.post(
        f'/api/cards/{card_id}/audio',
        files={'file': ('x.mp3', b'12345', 'audio/mpeg')},
    )
    assert up.status_code == 413


@pytest.mark.asyncio
async def test_send_card_audio_to_telegram_success(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    from services.cards import attach_user_card_audio as attach_audio_mod
    from services.cards import send_user_card_audio_to_telegram as send_audio_mod

    async def fake_upload_execute(
        self: object,
        *,
        user_id,
        content_type,
        data: bytes,
    ) -> str:
        return '/api/cards/media/user_media/movie_card_audio/fake-user/fakefile.mp3'

    monkeypatch.setattr(attach_audio_mod.UploadUserCardAudioService, 'execute', fake_upload_execute)

    async def fake_load_bytes(_rustfs_key: str) -> tuple[bytes, str]:
        return b'id3fake', 'audio/mpeg'

    monkeypatch.setattr(send_audio_mod, 'load_user_card_audio_media_bytes', fake_load_bytes)

    await _login(async_client, telegram_user_id=880020)
    film = await _create_film(kinopoisk_id=8800202)
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
    card_id = int(created.json()['id'])
    up = await async_client.post(
        f'/api/cards/{card_id}/audio',
        files={'file': ('x.mp3', b'id3fake', 'audio/mpeg')},
    )
    assert up.status_code == 200

    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(ok=True, payload={'ok': True, 'result': {}})
        r = await async_client.post(f'/api/cards/{card_id}/audio/send-telegram')

    assert r.status_code == 200
    assert r.json() == {'status': 'sent'}
    assert m.await_count == 1
    args, kwargs = m.call_args
    assert args[0] == 880020
    assert args[1] == b'id3fake'
    assert kwargs['filename'].endswith('.mp3')
    assert kwargs['content_type'] == 'audio/mpeg'


@pytest.mark.asyncio
async def test_send_card_audio_to_telegram_no_audio(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=880021)
    film = await _create_film(kinopoisk_id=8800212)
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
    card_id = int(created.json()['id'])
    r = await async_client.post(f'/api/cards/{card_id}/audio/send-telegram')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_send_card_audio_to_telegram_card_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=880022)
    r = await async_client.post('/api/cards/999999999/audio/send-telegram')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_send_card_audio_to_telegram_chat_unavailable(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    from services.cards import attach_user_card_audio as attach_audio_mod
    from services.cards import send_user_card_audio_to_telegram as send_audio_mod

    async def fake_upload_execute(
        self: object,
        *,
        user_id,
        content_type,
        data: bytes,
    ) -> str:
        return '/api/cards/media/user_media/movie_card_audio/fake-user/fakefile.mp3'

    monkeypatch.setattr(attach_audio_mod.UploadUserCardAudioService, 'execute', fake_upload_execute)

    async def fake_load_bytes(_rustfs_key: str) -> tuple[bytes, str]:
        return b'id3', 'audio/mpeg'

    monkeypatch.setattr(send_audio_mod, 'load_user_card_audio_media_bytes', fake_load_bytes)

    await _login(async_client, telegram_user_id=880023)
    film = await _create_film(kinopoisk_id=8800233)
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
    card_id = int(created.json()['id'])
    assert (
        await async_client.post(
            f'/api/cards/{card_id}/audio',
            files={'file': ('x.mp3', b'id3', 'audio/mpeg')},
        )
    ).status_code == 200

    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(
            ok=False,
            payload={
                'ok': False,
                'error_code': 403,
                'description': "Forbidden: bot can't initiate conversation with the user",
            },
        )
        r = await async_client.post(f'/api/cards/{card_id}/audio/send-telegram')

    assert r.status_code == 422
    detail = r.json()['detail']
    assert detail['code'] == 'telegram_chat_unavailable'
    assert 'bot_username' in detail
