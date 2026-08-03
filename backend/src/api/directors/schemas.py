from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DirectorSummaryResponse(BaseModel):
    kinopoisk_id: int
    name: str
    films_count: int
    avg_community_rating: float | None = None

    model_config = ConfigDict(extra='forbid')


class DirectorFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None = None
    poster_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    community_avg_rating: float | None = None
    ratings_count: int
    my_card_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class DirectorFilmsPageResponse(BaseModel):
    items: list[DirectorFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')
