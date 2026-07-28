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
from providers.youtube.youtube_oembed_client import YoutubeOembedClient
from services.kinopoisk.client import KinopoiskClientError
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
async def test_catalog_resolve_by_url_kinopoisk_happy_path(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=703)

    async def fake_get_film(self: object, kinopoisk_id: int):
        from services.kinopoisk.client import KinopoiskFilmPayload

        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title='Resolve By Url',
            year=2022,
            poster_url='https://example.com/by-url.jpg',
            genres=['драма'],
            short_description='Краткое.',
            description='Полное.',
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://kinopoisk.ru/film/888001/'},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == '888001'
    assert body['kind'] == 'film'
    assert body['title'] == 'Resolve By Url'
    assert body['cover_url'] == 'https://example.com/by-url.jpg'
    assert body['summary'] == 'Краткое.'
    assert body['film']['kinopoisk_id'] == 888001
    assert body['catalog_item_id'] >= 1


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_unknown_host_returns_422(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=704)
    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://letterboxd.com/film/matrix/'},
    )
    assert r.status_code == 422
    assert r.json()['detail'] == 'unsupported url host'


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_not_found_returns_404(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=705)

    async def missing_film(self: object, kinopoisk_id: int):
        _ = (self, kinopoisk_id)
        raise KinopoiskClientError('kinopoisk returned 404')

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', missing_film)

    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://www.kinopoisk.ru/film/999404/'},
    )
    assert r.status_code == 404
    assert r.json()['detail'] == 'catalog item not found'


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_youtube_happy_path(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=706)

    video_id = 'dQw4w9WgXcQ'
    canonical_url = f'https://www.youtube.com/watch?v={video_id}'

    async def fake_fetch(self: YoutubeOembedClient, video_url: str):
        assert video_url == canonical_url
        from providers.youtube.youtube_oembed_client import YoutubeOembedDTO

        return YoutubeOembedDTO(
            title='Test Video',
            thumbnail_url='https://i.ytimg.com/vi/abc/hqdefault.jpg',
            author_name='Test Channel',
        )

    monkeypatch.setattr(YoutubeOembedClient, 'fetch', fake_fetch)

    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': f'https://youtu.be/{video_id}'},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['provider'] == 'youtube'
    assert body['external_id'] == video_id
    assert body['kind'] == 'video'
    assert body['title'] == 'Test Video'
    assert body['cover_url'] == 'https://i.ytimg.com/vi/abc/hqdefault.jpg'
    assert body['summary'] == 'Test Channel'
    assert body['catalog_item_id'] is None
    assert body['film'] is None
    assert body['source_url'] == canonical_url
    assert body['my_card_id'] is None


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_youtube_bad_video_returns_404(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=707)

    async def missing_video(self: YoutubeOembedClient, video_url: str):
        _ = (self, video_url)
        raise YoutubeOembedClient.VideoNotFoundError

    monkeypatch.setattr(YoutubeOembedClient, 'fetch', missing_video)

    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
    )
    assert r.status_code == 404
    assert r.json()['detail'] == 'catalog item not found'


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_youtube_oembed_failure_returns_502(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=708)

    async def failing_oembed(self: YoutubeOembedClient, video_url: str):
        _ = (self, video_url)
        raise YoutubeOembedClient.UpstreamError('upstream unavailable')

    monkeypatch.setattr(YoutubeOembedClient, 'fetch', failing_oembed)

    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
    )
    assert r.status_code == 502
    assert r.json()['detail'] == 'upstream unavailable'


@pytest.mark.asyncio
async def test_catalog_resolve_by_url_youtube_invalid_url_returns_422(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=709)
    r = await async_client.post(
        '/api/catalog/resolve-by-url',
        json={'url': 'https://www.youtube.com/watch'},
    )
    assert r.status_code == 422
    assert r.json()['detail'] == 'unsupported youtube url'


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


@pytest.mark.asyncio
async def test_catalog_candidates_mixed_sources(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71401)

    remote_film = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 714_101,
            'nameRu': 'Mixed Candidate Film',
            'year': '2020',
            'posterUrl': 'https://example.com/film.jpg',
            'description': None,
            'type': 'FILM',
        },
    )

    async def fake_kp_search(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        _ = (self, page)
        assert keyword == 'mixedcandidates'
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=1,
            films=(remote_film,),
        )

    rawg_doc = RawgGamesListResponseDTO.from_document(
        {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 714_102,
                    'slug': 'mixed-game',
                    'name': 'Mixed Candidate Game',
                    'released': '2021-01-01',
                    'tba': False,
                    'background_image': 'https://example.com/game.jpg',
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
        },
    )

    async def fake_rawg_search(
        _self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        assert params.search == 'mixedcandidates'
        return rawg_doc

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_kp_search)
    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_rawg_search)

    r = await async_client.get(
        '/api/catalog/candidates',
        params={'q': 'MixedCandidates', 'limit': 10},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['meta']['degraded_sources'] == []
    assert len(body['items']) == 2

    kinds = {item['kind'] for item in body['items']}
    assert kinds == {'film', 'game'}

    for item in body['items']:
        assert item['candidate_id'] == f'{item["provider"]}:{item["external_id"]}'
        assert item['kind_hint'] == item['kind']

    film_item = next(i for i in body['items'] if i['kind'] == 'film')
    game_item = next(i for i in body['items'] if i['kind'] == 'game')
    assert film_item['external_id'] == '714101'
    assert game_item['external_id'] == '714102'
    assert film_item['source'] == 'remote'
    assert game_item['source'] == 'remote'


@pytest.mark.asyncio
async def test_catalog_candidates_query_too_short_returns_empty(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=71402)
    r = await async_client.get('/api/catalog/candidates', params={'q': '  ab '})
    assert r.status_code == 200
    body = r.json()
    assert body['items'] == []
    assert body['has_more'] is False
    assert body['meta']['degraded_sources'] == []


@pytest.mark.asyncio
async def test_catalog_candidates_one_source_degraded(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71403)

    async def fake_kp_search(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        _ = (self, page)
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=0,
            films=(),
        )

    async def failing_rawg(
        _self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        _ = params
        raise RawgProviderTransport.RawgProviderTransportError(msg='RAWG timeout')

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_kp_search)
    monkeypatch.setattr(RawgProviderTransport, 'search_games', failing_rawg)

    r = await async_client.get(
        '/api/catalog/candidates',
        params={'q': 'DegradedOne', 'limit': 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['meta']['degraded_sources'] == ['rawg']


@pytest.mark.asyncio
async def test_catalog_candidates_same_title_film_and_game_both_returned(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=71404)

    title = 'Shared Title Token'

    remote_film = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 714_201,
            'nameRu': title,
            'year': '2018',
            'posterUrl': None,
            'description': None,
            'type': 'FILM',
        },
    )

    async def fake_kp_search(self: KinopoiskProviderTransport, keyword: str, page: int = 1):
        _ = (self, page)
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=1,
            films=(remote_film,),
        )

    rawg_doc = RawgGamesListResponseDTO.from_document(
        {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 714_202,
                    'slug': 'shared-title',
                    'name': title,
                    'released': None,
                    'tba': False,
                    'background_image': None,
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
        },
    )

    async def fake_rawg_search(
        _self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        return rawg_doc

    monkeypatch.setattr(KinopoiskProviderTransport, 'search_films_by_keyword', fake_kp_search)
    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_rawg_search)

    r = await async_client.get(
        '/api/catalog/candidates',
        params={'q': 'SharedTitleToken', 'limit': 10},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body['items']) == 2
    assert {item['title'] for item in body['items']} == {title}
    assert {item['kind'] for item in body['items']} == {'film', 'game'}
