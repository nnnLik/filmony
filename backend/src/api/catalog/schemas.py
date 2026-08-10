from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.films.schemas import FilmResponse
from models.catalog_item import CatalogProvider


class CatalogSearchProvider(StrEnum):
    """Catalog providers supported by ``GET /catalog/search`` (excludes ``no_provider``)."""

    kinopoisk = 'kinopoisk'
    rawg = 'rawg'


CatalogSearchHitKind = Literal['film', 'game']
CatalogSearchHitSource = Literal['local', 'remote']
CatalogDetailKind = Literal['film', 'game']


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


class CatalogCandidateResponse(BaseModel):
    candidate_id: str
    provider: CatalogProvider
    external_id: str
    kind: CatalogSearchHitKind
    kind_hint: CatalogSearchHitKind | None = None
    title: str
    subtitle: str | None = None
    cover_url: str | None = None
    catalog_item_id: int | None = None
    source: CatalogSearchHitSource
    degraded: bool | None = None


class CatalogCandidatesMetaResponse(BaseModel):
    degraded_sources: list[str] = Field(default_factory=list)


class CatalogCandidatesResponse(BaseModel):
    items: list[CatalogCandidateResponse]
    has_more: bool
    meta: CatalogCandidatesMetaResponse


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


class CatalogResolveByUrlRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class CatalogResolveByUrlResponse(BaseModel):
    provider: CatalogProvider
    external_id: str
    kind: Literal['film', 'video']
    title: str
    cover_url: str | None = None
    summary: str | None = None
    catalog_item_id: int | None = None
    film: FilmResponse | None = None
    source_url: str | None = None
    my_card_id: int | None = None


class CatalogItemDetailResponse(BaseModel):
    catalog_item_id: int
    provider: CatalogProvider
    external_id: str
    kind: CatalogDetailKind
    title: str
    year: int | None = None
    poster_url: str | None = None
    short_description: str | None = None
    description: str | None = None
    film_id: int | None = None
    game_id: int | None = None
    genres: list[str] = Field(default_factory=list)
    my_card_id: int | None = Field(
        default=None,
        description='Id карточки текущего пользователя для этого тайтла, если уже оценивал',
    )


class CatalogCommunityAuthorResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    display_name: str | None = None


class CatalogCommunityCardItemResponse(BaseModel):
    id: int
    author: CatalogCommunityAuthorResponse
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str = ''
    custom_tags: list[str] = Field(default_factory=list)
    updated_at: datetime
    is_favorite: bool = False


class CatalogCommunityCardsPageResponse(BaseModel):
    items: list[CatalogCommunityCardItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class CatalogFilmsSort(StrEnum):
    popularity = 'popularity'
    avg_rating = 'avg_rating'


class CatalogFilmsPeriod(StrEnum):
    all_time = 'all_time'
    month = 'month'


class CatalogFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str] = Field(default_factory=list)
    community_avg_rating: float | None
    ratings_count: int
    my_card_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class CatalogFilmsPageResponse(BaseModel):
    items: list[CatalogFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')
