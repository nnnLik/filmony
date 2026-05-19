from __future__ import annotations

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.game import Game
from providers.rawg.rawg_openapi_dto import RawgGamesListQueryParams, RawgGamesListResponseDTO
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from services.catalog.ensure_rawg_catalog_item_service import EnsureRawgCatalogItemService
from services.catalog.search_rawg_catalog_games_service import SearchRawgCatalogGamesService


@pytest.mark.asyncio
async def test_search_rawg_catalog_local_only_ensures_catalog_item(prepare_db: None) -> None:
    sf = get_session_factory()
    async with sf() as session:
        session.add(Game(rawg_id=900010, name='Local Cyber Quest'))
        await session.commit()

    async with sf() as session:
        result = await SearchRawgCatalogGamesService.build(session).execute(
            'Cyber Quest', 15, allow_remote=False
        )
    hits = result.hits
    assert len(hits) == 1
    h = hits[0]
    assert h.source == 'local'
    assert h.kind == 'game'
    assert h.provider == CatalogProvider.rawg
    assert h.external_id == '900010'
    assert h.title == 'Local Cyber Quest'
    assert h.catalog_item_id >= 1

    async with sf() as session:
        row = (
            await session.scalars(select(CatalogItem).where(CatalogItem.id == h.catalog_item_id))
        ).one()
        assert row.provider == CatalogProvider.rawg
        assert row.external_id == '900010'
        assert row.game_id is not None


@pytest.mark.asyncio
async def test_search_rawg_catalog_remote_persists_and_links_catalog_item(
    monkeypatch: pytest.MonkeyPatch, prepare_db: None
) -> None:
    list_doc = {
        'count': 2,
        'results': [
            {
                'id': 900020,
                'slug': 'alpha-k',
                'name': 'Alpha K',
                'released': None,
                'tba': False,
                'background_image': 'https://example.com/a.jpg',
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
            {
                'id': 900021,
                'slug': 'beta-k',
                'name': 'Beta Kappa',
                'released': '2020-01-01',
                'tba': False,
                'background_image': None,
                'rating': 3.14,
                'rating_top': 5,
                'ratings': {},
                'ratings_count': None,
                'reviews_text_count': None,
                'added': None,
                'added_by_status': {},
                'metacritic': 80,
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
        self: RawgProviderTransport, params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        assert params.search == 'kappamix'
        return dto

    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_search)

    sf = get_session_factory()
    async with sf() as session:
        result = await SearchRawgCatalogGamesService.build(
            session, RawgProviderTransport()
        ).execute('KappaMix', 5, allow_remote=True)
    hits = result.hits
    assert len(hits) == 2
    assert {h.external_id for h in hits} == {'900020', '900021'}
    assert all(h.source == 'remote' for h in hits)

    async with sf() as session:
        g1 = (await session.scalars(select(Game).where(Game.rawg_id == 900020))).one()
        assert g1.name == 'Alpha K'
        ci1 = (
            await session.scalars(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.rawg,
                    CatalogItem.external_id == '900020',
                )
            )
        ).one()
        assert ci1.game_id == g1.id


@pytest.mark.asyncio
async def test_search_rawg_catalog_dedupes_remote_against_local(
    monkeypatch: pytest.MonkeyPatch, prepare_db: None
) -> None:
    overlap_id = 900030
    list_doc = {
        'count': 2,
        'results': [
            {
                'id': overlap_id,
                'slug': 'overlap',
                'name': 'Overlap Tale',
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
            {
                'id': 900031,
                'slug': 'unique-remote',
                'name': 'Unique Remote',
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
    }
    dto = RawgGamesListResponseDTO.from_document(list_doc)

    async def fake_search(
        self: RawgProviderTransport, _params: RawgGamesListQueryParams
    ) -> RawgGamesListResponseDTO:
        return dto

    monkeypatch.setattr(RawgProviderTransport, 'search_games', fake_search)

    sf = get_session_factory()
    async with sf() as session:
        session.add(Game(rawg_id=overlap_id, name='Overlap Tale Local'))
        await session.commit()

    async with sf() as session:
        result = await SearchRawgCatalogGamesService.build(
            session, RawgProviderTransport()
        ).execute('Overlap', 5, allow_remote=True)
        hits = result.hits

    ids = {(h.external_id, h.source) for h in hits}
    assert len(hits) == 2
    assert ('900031', 'remote') in ids
    overlap_hits = [h for h in hits if h.external_id == str(overlap_id)]
    assert len(overlap_hits) == 1
    assert overlap_hits[0].source == 'local'


@pytest.mark.asyncio
async def test_ensure_rawg_catalog_item_idempotent_on_same_game(prepare_db: None) -> None:
    sf = get_session_factory()
    async with sf() as session:
        game = Game(rawg_id=900050, name='Stable Item')
        session.add(game)
        await session.flush()
        svc = EnsureRawgCatalogItemService.build(session)
        ci1 = await svc.execute(game=game)
        ci2 = await svc.execute(game=game)
        await session.commit()

    assert ci1.id == ci2.id
