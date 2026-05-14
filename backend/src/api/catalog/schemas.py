from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from api.films.schemas import FilmResponse
from models.catalog_item import CatalogProvider


class CatalogSearchProvider(StrEnum):
    """Catalog providers supported by ``GET /catalog/search`` (excludes ``no_provider``)."""

    kinopoisk = 'kinopoisk'
    rawg = 'rawg'


CatalogSearchHitKind = Literal['film', 'game']
CatalogSearchHitSource = Literal['local', 'remote']


class CatalogSearchHitResponse(BaseModel):
    provider: CatalogProvider
    external_id: str
    kind: CatalogSearchHitKind
    title: str
    subtitle: str | None = None
    cover_url: str | None = None
    catalog_item_id: int | None = None
    source: CatalogSearchHitSource


class CatalogSearchResponse(BaseModel):
    items: list[CatalogSearchHitResponse]
    has_more: bool


class CatalogResolveRequest(BaseModel):
    provider: CatalogProvider
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class CatalogResolveResponse(BaseModel):
    catalog_item_id: int
    provider: CatalogProvider
    external_id: str
    title: str
    cover_url: str | None = None
    summary: str | None = None
    film: FilmResponse
