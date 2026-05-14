from __future__ import annotations

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from providers.kinopoisk.kinopoisk_search_dto import (
    KinopoiskFilmSearchItemDTO,
    KinopoiskFilmSearchResponseDTO,
)
from services.catalog.search_kinopoisk_films_local_first import (
    PAGE_SIZE,
    SearchKinopoiskFilmsLocalFirstService,
)


class ExplodingKinopoiskTransport:
    async def search_films_by_keyword(
        self, keyword: str, page: int = 1
    ) -> KinopoiskFilmSearchResponseDTO:
        _ = (keyword, page)
        raise AssertionError('Kinopoisk search API must not be called')


@pytest.mark.asyncio
async def test_skips_remote_when_local_matches_fill_first_page(
    prepare_db: None,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        for i in range(PAGE_SIZE):
            session.add(
                Film(
                    kinopoisk_id=50_000 + i,
                    title=f'QueryTok Local {i}',
                    year=2020,
                    poster_url=None,
                    genres=[],
                    short_description=None,
                    description=None,
                ),
            )
        await session.commit()

    async with session_factory() as session:
        svc = SearchKinopoiskFilmsLocalFirstService.build(
            session,
            transport=ExplodingKinopoiskTransport(),
        )
        result = await svc.execute('QueryTok')
        assert len(result.hits) == PAGE_SIZE
        assert all(h.source == 'local' for h in result.hits)
        assert result.has_more is False


@pytest.mark.asyncio
async def test_remote_fallback_persists_film_and_catalog_item(
    prepare_db: None,
) -> None:
    remote_item = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 263531,
            'nameRu': 'Мстители',
            'year': '2012',
            'posterUrl': 'https://example.com/poster.jpg',
            'description': 'Страна, режиссёр',
            'type': 'FILM',
        },
    )
    remote = KinopoiskFilmSearchResponseDTO(
        keyword='мстители',
        pages_count=1,
        search_films_count_result=1,
        films=(remote_item,),
    )

    class FakeTransport:
        async def search_films_by_keyword(self, keyword: str, page: int = 1):
            _ = (keyword, page)
            return remote

    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SearchKinopoiskFilmsLocalFirstService.build(session, transport=FakeTransport())
        result = await svc.execute('  мстители  ')
        assert len(result.hits) == 1
        hit = result.hits[0]
        assert hit.source == 'provider'
        assert hit.kinopoisk_id == 263531
        assert hit.catalog_item_id is not None

    async with session_factory() as session:
        film = (await session.execute(select(Film).where(Film.kinopoisk_id == 263531))).scalar_one()
        assert film.title == 'Мстители'
        row = (
            await session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.kinopoisk,
                    CatalogItem.external_id == '263531',
                ),
            )
        ).scalar_one()
        assert row.film_id == film.id


@pytest.mark.asyncio
async def test_merges_local_then_remote_without_duplicate_kinopoisk_ids(
    prepare_db: None,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            Film(
                kinopoisk_id=100,
                title='Alpha QueryTok Beta',
                year=1999,
                poster_url=None,
                genres=['драма'],
                short_description=None,
                description=None,
            ),
        )
        await session.commit()

    remote_item = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 100,
            'nameRu': 'Duplicate',
            'year': '1999',
            'posterUrl': 'https://example.com/a.jpg',
            'type': 'FILM',
        },
    )
    remote_item_b = KinopoiskFilmSearchItemDTO.from_dict(
        {
            'filmId': 200,
            'nameRu': 'Remote only',
            'year': '2001',
            'posterUrl': 'https://example.com/b.jpg',
            'type': 'FILM',
        },
    )
    remote = KinopoiskFilmSearchResponseDTO(
        keyword='q',
        pages_count=1,
        search_films_count_result=2,
        films=(remote_item, remote_item_b),
    )

    class FakeTransport:
        async def search_films_by_keyword(self, keyword: str, page: int = 1):
            _ = (keyword, page)
            return remote

    async with session_factory() as session:
        svc = SearchKinopoiskFilmsLocalFirstService.build(session, transport=FakeTransport())
        result = await svc.execute('QueryTok')
        kp_ids = [h.kinopoisk_id for h in result.hits]
        assert kp_ids == [100, 200]
        sources = [h.source for h in result.hits]
        assert sources == ['local', 'provider']
