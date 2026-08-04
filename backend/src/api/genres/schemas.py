from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GenreCatalogItemResponse(BaseModel):
    slug: str
    genre: str
    films_count: int

    model_config = ConfigDict(extra='forbid')


class GenresCatalogPageResponse(BaseModel):
    items: list[GenreCatalogItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')


class GenreSummaryResponse(BaseModel):
    slug: str
    genre: str
    films_count: int
    avg_community_rating: float | None = None
    top_genres: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class GenreFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str] = Field(default_factory=list)
    community_avg_rating: float | None
    ratings_count: int
    my_card_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class GenreFilmsPageResponse(BaseModel):
    items: list[GenreFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')
