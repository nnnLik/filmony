from __future__ import annotations

import pytest

from models.catalog_item import CatalogProvider
from providers.kinopoisk.kinopoisk_search_dto import (
    KinopoiskFilmSearchItemDTO,
    KinopoiskFilmSearchResponseDTO,
)
from providers.rawg.rawg_openapi_dto import RawgGamesListQueryParams, RawgGamesListResponseDTO
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from services.catalog.search_catalog_candidates_service import SearchCatalogCandidatesService
from services.catalog.search_kinopoisk_films_local_first import (
    SearchKinopoiskFilmsLocalFirstService,
)
from services.catalog.search_rawg_catalog_games_service import SearchRawgCatalogGamesService


class FakeKinopoiskTransport:
    def __init__(self, *, films: tuple[KinopoiskFilmSearchItemDTO, ...] = ()) -> None:
        self._films = films
        self.calls: list[str] = []

    async def search_films_by_keyword(self, keyword: str, page: int = 1):
        _ = page
        self.calls.append(keyword)
        return KinopoiskFilmSearchResponseDTO(
            keyword=keyword,
            pages_count=1,
            search_films_count_result=len(self._films),
            films=self._films,
        )


class FailingRawgTransport:
    async def search_games(self, params: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
        _ = params
        raise RawgProviderTransport.RawgProviderTransportError(msg='RAWG down')


@pytest.mark.asyncio
async def test_merge_mixed_sources_local_before_remote(prepare_db: None) -> None:
    from core.database import get_session_factory
    from models.film import Film
    from models.game import Game

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Film(
                kinopoisk_id=880_001,
                title='Castlevania Film Local',
                year=2020,
                poster_url=None,
                genres=[],
                short_description=None,
                description=None,
            ),
        )
        session.add(
            Game(rawg_id=880_002, name='Castlevania Game Local', slug=None, released=None),
        )
        await session.commit()

    kp_transport = FakeKinopoiskTransport(
        films=(
            KinopoiskFilmSearchItemDTO.from_dict(
                {
                    'filmId': 880_003,
                    'nameRu': 'Castlevania Film Remote',
                    'year': '2019',
                    'posterUrl': None,
                    'description': None,
                    'type': 'FILM',
                },
            ),
        ),
    )

    rawg_doc = RawgGamesListResponseDTO.from_document(
        {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 880_004,
                    'slug': 'castlevania-remote',
                    'name': 'Castlevania Game Remote',
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

    class FakeRawgTransport:
        async def search_games(self, params: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
            assert params.search == 'castlevania'
            return rawg_doc

    async with session_factory() as session:
        svc = SearchCatalogCandidatesService.build(
            session,
            kinopoisk_transport=kp_transport,
            rawg_transport=FakeRawgTransport(),
        )
        result = await svc.execute('Castlevania', limit=10)

    assert result.degraded_sources == ()
    assert len(result.items) == 4
    titles = [item.title for item in result.items]
    assert 'Castlevania Film Local' in titles
    assert 'Castlevania Game Local' in titles
    assert 'Castlevania Film Remote' in titles
    assert 'Castlevania Game Remote' in titles

    local_indices = [i for i, item in enumerate(result.items) if item.source == 'local']
    remote_indices = [i for i, item in enumerate(result.items) if item.source == 'remote']
    assert local_indices and remote_indices
    assert max(local_indices) < min(remote_indices)

    film_rows = [item for item in result.items if item.kind == 'film']
    game_rows = [item for item in result.items if item.kind == 'game']
    assert len(film_rows) == 2
    assert len(game_rows) == 2
    assert all(
        item.candidate_id == f'{item.provider.value}:{item.external_id}' for item in result.items
    )
    assert all(item.kind_hint == item.kind for item in result.items)


@pytest.mark.asyncio
async def test_query_shorter_than_three_returns_empty(prepare_db: None) -> None:
    from core.database import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SearchCatalogCandidatesService.build(session)
        result = await svc.execute('  ab  ')

    assert result.items == ()
    assert result.has_more is False
    assert result.degraded_sources == ()


@pytest.mark.asyncio
async def test_query_three_chars_skips_rawg(prepare_db: None) -> None:
    from core.database import get_session_factory

    kp_transport = FakeKinopoiskTransport()

    class ExplodingRawgTransport:
        async def search_games(self, params: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
            _ = params
            raise AssertionError('RAWG must not be called for 3-char query')

    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SearchCatalogCandidatesService.build(
            session,
            kinopoisk_transport=kp_transport,
            rawg_transport=ExplodingRawgTransport(),
        )
        result = await svc.execute('abc')

    assert result.degraded_sources == ()
    assert kp_transport.calls == ['abc']


@pytest.mark.asyncio
async def test_one_source_failure_still_returns_other_hits(prepare_db: None) -> None:
    from core.database import get_session_factory

    kp_transport = FakeKinopoiskTransport(
        films=(
            KinopoiskFilmSearchItemDTO.from_dict(
                {
                    'filmId': 881_002,
                    'nameRu': 'Solo Kinopoisk Hit',
                    'year': '2020',
                    'posterUrl': None,
                    'description': None,
                    'type': 'FILM',
                },
            ),
        ),
    )

    class FailingRawg:
        async def search_games(self, params: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
            _ = params
            raise RawgProviderTransport.RawgProviderTransportError(msg='timeout')

    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SearchCatalogCandidatesService.build(
            session,
            kinopoisk_transport=kp_transport,
            rawg_transport=FailingRawg(),
        )
        result = await svc.execute('SoloKinopoiskHit', limit=5)

    assert 'rawg' in result.degraded_sources
    assert 'kinopoisk' not in result.degraded_sources
    assert any(item.provider == CatalogProvider.kinopoisk for item in result.items)


@pytest.mark.asyncio
async def test_both_sources_fail_returns_empty_items(prepare_db: None) -> None:
    from core.database import get_session_factory
    from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport

    class FailingKp:
        async def search_films_by_keyword(self, keyword: str, page: int = 1):
            _ = (keyword, page)
            raise KinopoiskProviderTransport.KinopoiskProviderTransportError(msg='kp down')

    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SearchCatalogCandidatesService.build(
            session,
            kinopoisk_transport=FailingKp(),
            rawg_transport=FailingRawgTransport(),
        )
        result = await svc.execute('bothfail query', limit=5)

    assert result.items == ()
    assert set(result.degraded_sources) == {'kinopoisk', 'rawg'}


@pytest.mark.asyncio
async def test_dedup_same_provider_external_id(prepare_db: None) -> None:
    from core.database import get_session_factory
    from services.catalog.search_catalog_candidates_service import _merge_candidates
    from services.catalog.search_kinopoisk_films_local_first import (
        CatalogFilmSearchHitDTO,
        SearchKinopoiskFilmsResult,
    )

    hit = CatalogFilmSearchHitDTO(
        provider=CatalogProvider.kinopoisk,
        external_id='123',
        kinopoisk_id=123,
        title='Dup',
        subtitle=None,
        cover_url=None,
        summary=None,
        film_id=1,
        catalog_item_id=1,
        source='local',
    )
    film_result = SearchKinopoiskFilmsResult(
        keyword='dup',
        page=1,
        pages_count=1,
        total_remote=1,
        hits=(hit, hit),
        has_more=False,
    )
    items, _ = _merge_candidates(film_result=film_result, game_result=None, limit=10)
    assert len(items) == 1
