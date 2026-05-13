from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.catalog.schemas import CatalogResolveRequest, CatalogResolveResponse
from api.films.schemas import FilmResponse
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.get_my_movie_card_id_for_film import GetMyMovieCardIdForFilmService
from services.catalog.resolve_catalog_item_service import ResolveCatalogItemService
from services.kinopoisk.resolve_kinopoisk_film import (
    KinopoiskClientError,
    KinopoiskUrlParseError,
)

router = APIRouter(prefix='/catalog', tags=['catalog'])


@router.post('/resolve', response_model=CatalogResolveResponse, summary='Резолв элемента каталога по URL провайдера')
async def resolve_catalog_item(
    body: CatalogResolveRequest,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogResolveResponse:
    try:
        catalog_item, film = await ResolveCatalogItemService.build(db).execute(
            provider=body.provider,
            url=body.url,
        )
    except ResolveCatalogItemService.UnsupportedCatalogProviderError as e:
        raise HTTPException(status_code=422, detail='unsupported catalog provider') from e
    except KinopoiskUrlParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except KinopoiskClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    my_card_id = await GetMyMovieCardIdForFilmService.build(db).execute(viewer.id, film.id)

    return CatalogResolveResponse(
        catalog_item_id=catalog_item.id,
        provider=catalog_item.provider,
        external_id=catalog_item.external_id,
        title=film.title,
        cover_url=film.poster_url,
        summary=film.short_description,
        film=FilmResponse(
            id=film.id,
            kinopoisk_id=film.kinopoisk_id,
            genres=list(film.genres or []),
            title=film.title,
            year=film.year,
            poster_url=film.poster_url,
            short_description=film.short_description,
            description=film.description,
            my_card_id=my_card_id,
        ),
    )
