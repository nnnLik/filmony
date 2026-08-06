from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from models.collection import CollectionKind


class UserCollectionProgressResponse(BaseModel):
    rated_count: int
    total_count: int
    completed_at: dt.datetime | None = None

    model_config = ConfigDict(extra='forbid')


class CollectionSummaryResponse(BaseModel):
    slug: str
    kind: CollectionKind
    title: str
    description: str | None = None
    season_year: int | None = None
    film_count: int
    content_updated_at: dt.datetime
    viewer_progress: UserCollectionProgressResponse | None = None
    is_pinned: bool | None = None

    model_config = ConfigDict(extra='forbid')


class CollectionListResponse(BaseModel):
    items: list[CollectionSummaryResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class CollectionFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None = None
    poster_url: str | None = None
    viewer_has_rated: bool | None = None
    viewer_card_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class CollectionFilmsPageResponse(BaseModel):
    items: list[CollectionFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None
    total_count: int

    model_config = ConfigDict(extra='forbid')


class ProfilePinnedCollectionsResponse(BaseModel):
    items: list[CollectionSummaryResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')
