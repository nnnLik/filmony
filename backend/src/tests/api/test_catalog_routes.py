from __future__ import annotations

import logging
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from providers.base_provider_http_transport import BaseProviderHttpTransport
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.kinopoisk.kinopoisk_search_dto import (
    KinopoiskFilmSearchItemDTO,
    KinopoiskFilmSearchResponseDTO,
)
from providers.rawg.rawg_openapi_dto import RawgGamesListQueryParams, RawgGamesListResponseDTO
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_catalog_resolve_kinopoisk_creates_catalog_item(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=700)

    async def fake_get_film(self: object, kinopoisk_id: int):
        from services.kinopoisk.client import KinopoiskFilmPayload

        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title='Каталог-тест',
            year=2021,
            poster_url='https://example.com/cat.jpg',
            genres=['комедия'],
            short_description='Кратко.',
            description='Полное описание.',
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'kinopoisk', 'url': 'https://www.kinopoisk.ru/film/777001/'},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == '777001'
    assert body['title'] == 'Каталог-тест'
    assert body['cover_url'] == 'https://example.com/cat.jpg'
    assert body['summary'] == 'Кратко.'
    assert body['film']['kinopoisk_id'] == 777001
    assert body['film']['title'] == 'Каталог-тест'
    catalog_item_id = body['catalog_item_id']

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(select(CatalogItem).where(CatalogItem.id == catalog_item_id))
        ).scalar_one()
        assert row.provider == CatalogProvider.kinopoisk
        assert row.external_id == '777001'
        film = (await session.execute(select(Film).where(Film.id == row.film_id))).scalar_one()
        assert film.kinopoisk_id == 777001


@pytest.mark.asyncio
async def test_catalog_resolve_unsupported_provider(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=701)
    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'letterboxd', 'url': 'https://letterboxd.com/film/matrix/'},
    )
    assert r.status_code == 422
    body = r.json()
    assert isinstance(body.get('detail'), list)
    detail = body['detail']
    assert detail
    locs = [tuple(e.get('loc', ())) for e in detail]
    assert any('provider' in loc for loc in locs)


@pytest.mark.asyncio
async def test_catalog_resolve_no_provider_returns_422(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=761030)
    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'no_provider', 'url': 'https://example.com/anything'},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_catalog_resolve_invalid_url(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=702)
    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'kinopoisk', 'url': 'https://example.com/not-kino'},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_catalog_search_rawg_local_only_no_remote_transport(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71301)

    async def exploding_search(_self: RawgProviderTransport, _params: RawgGamesListQueryParams):
        raise AssertionError('RAWG HTTP search must not be called when limit is saturated locally')

    monkeypatch.setattr(RawgProviderTransport, 'search_games', exploding_search)

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Game(rawg_id=913_001, name='CryoApiRawg TokenOne', slug=None, released=None),
        )
        await session.commit()

    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'rawg', 'q': 'CryoApiRawg', 'limit': 1},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['has_more'] is True
    assert len(body['items']) == 1
    item = body['items'][0]
    assert item['provider'] == 'rawg'
    assert item['kind'] == 'game'
    assert item['external_id'] == '913001'
    assert item['title'] == 'CryoApiRawg TokenOne'
    assert item['source'] == 'local'
    assert item['catalog_item_id'] >= 1


@pytest.mark.asyncio
async def test_catalog_search_rawg_transport_failure_502_non_empty_detail(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    await _login(async_client, telegram_user_id=71307)

    inner = BaseProviderHttpTransport.ProviderUnexpectedStatusError(
        msg='unexpected status 401',
        status_code=HTTPStatus.UNAUTHORIZED,
    )

    async def failing_search(_self: RawgProviderTransport, _params: RawgGamesListQueryParams):
        raise RawgProviderTransport.RawgProviderTransportError(
            msg='RAWG games search: unexpected status 401',
        ) from inner

    monkeypatch.setattr(RawgProviderTransport, 'search_games', failing_search)

    with caplog.at_level(logging.ERROR):
        r = await async_client.get(
            '/api/catalog/search',
            params={'provider': 'rawg', 'q': 'CryoRawgFail', 'limit': 5},
        )
    assert r.status_code == 502
    body = r.json()
    assert isinstance(body.get('detail'), str)
    assert body['detail'].strip() == 'RAWG games search: unexpected status 401'

    assert any(rec.msg == 'RAWG catalog search failed' for rec in caplog.records)
    assert 'RawgProviderTransportError: RAWG games search: unexpected status 401' in caplog.text
    assert 'ProviderUnexpectedStatusError' in caplog.text


@pytest.mark.asyncio
async def test_catalog_search_rawg_remote_persists_via_transport(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71302)

    list_doc = {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {
                'id': 913_002,
                'slug': 'cryo-remote',
                'name': 'Cryo Remote Shard',
                'released': None,
                'tba': False,
                'background_image': 'https://example.com/rawg-cover.jpg',
                'rating': 0.0,
                'rating_top': None,
                'ratings': {},
                'ratings_count': None,
                'reviews_text_count': None,
                'added': None,
                'added_by_status': {},
                'metacritic': None,
                'playtime': None,
                'suggestions_count': None,
                'updated': None,
                'esrb_rating': None,
                'platforms': [],
            },
        ],
    }
    dto = RawgGamesListResponseDTO.from_document(list_doc)

    async def fake_search(
        _self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        assert params.search == 'cryoremoteqwerty'
        return dto

    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_search)

    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'rawg', 'q': 'CryoRemoteQwerty', 'limit': 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body['items']) == 1
    item = body['items'][0]
    assert item['source'] == 'remote'
    assert item['catalog_item_id'] >= 1
    assert item['cover_url'] == 'https://example.com/rawg-cover.jpg'

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.rawg,
                    CatalogItem.external_id == str(913_002),
                ),
            )
        ).scalar_one()
        assert row.game_id is not None


@pytest.mark.asyncio
async def test_catalog_search_kinopoisk_local_only_empty_remote(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71303)

    async def fake_empty(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=0,
            films=(),
        )

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_empty)

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Film(
                kinopoisk_id=713_051,
                title='CryoApiKp Solo Film Alpha',
                year=2015,
                poster_url=None,
                genres=[],
                short_description=None,
                description=None,
            ),
        )
        await session.commit()

    r = await async_client.get(
        '/api/catalog/search', params={'provider': 'kinopoisk', 'q': 'CryoApiKp', 'limit': 10}
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body['items']) >= 1
    first = body['items'][0]
    assert first['provider'] == 'kinopoisk'
    assert first['kind'] == 'film'
    assert first['external_id'] == '713051'
    assert first['source'] == 'local'


@pytest.mark.asyncio
async def test_catalog_search_kinopoisk_remote_persists_via_transport(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71304)

    remote_item = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 713_099,
            'nameRu': 'Cryo Kp Remote API',
            'year': '2019',
            'posterUrl': 'https://example.com/kp-remote.jpg',
            'description': 'Synopsis.',
            'type': 'FILM',
        },
    )
    remote = KinopoiskFilmSearchResponseDTO(
        keyword='cryoremotekp',
        pages_count=1,
        search_films_count_result=1,
        films=(remote_item,),
    )

    async def fake_search(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        _ = (self, page)
        assert keyword == 'cryokpremote xyz'
        return remote

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_search)

    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'kinopoisk', 'q': 'CryoKpRemote XYZ', 'limit': 15},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body['items']) == 1
    item = body['items'][0]
    assert item['source'] == 'remote'
    assert item['catalog_item_id'] is not None
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.kinopoisk,
                    CatalogItem.external_id == str(713_099),
                ),
            )
        ).scalar_one()
        assert row.film_id is not None


@pytest.mark.asyncio
async def test_catalog_search_no_provider_returns_422(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71305)
    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'no_provider', 'q': 'abc'},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_catalog_search_query_too_short_after_trim(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71306)
    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'rawg', 'q': '  xx  '},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_catalog_search_rawg_query_three_chars_returns_422(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=71309)
    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'rawg', 'q': 'abc'},
    )
    assert r.status_code == 422
    body = r.json()
    assert (
        body.get('detail')
        == 'Query must contain at least 4 non-whitespace characters for RAWG search'
    )


@pytest.mark.asyncio
async def test_catalog_search_rawg_passes_normalized_lowercase_to_transport(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71320)

    seen: list[str] = []

    async def fake_search(
        _self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        seen.append(params.search or '')
        return RawgGamesListResponseDTO.from_document(
            {'count': 0, 'next': None, 'previous': None, 'results': []},
        )

    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_search)

    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'rawg', 'q': '  AbCdEfGh  ', 'limit': 5},
    )
    assert r.status_code == 200
    assert r.json()['items'] == []
    assert seen == ['abcdefgh']


@pytest.mark.asyncio
async def test_catalog_search_kinopoisk_passes_normalized_lowercase_to_transport(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71321)

    seen: list[str] = []

    async def fake_search(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        _ = (self, page)
        seen.append(keyword)
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=0,
            films=(),
        )

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_search)

    r = await async_client.get(
        '/api/catalog/search',
        params={'provider': 'kinopoisk', 'q': '  XyZ   AbC ', 'limit': 5},
    )
    assert r.status_code == 200
    assert seen == ['xyz abc']
