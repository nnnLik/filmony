from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActorSummaryResponse(BaseModel):
    kinopoisk_id: int
    name: str
    poster_url: str | None = None
    films_count: int

    model_config = ConfigDict(extra='forbid')


class ActorFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None = None
    poster_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    role: str | None = None
    my_card_id: int | None = None
    rating: float | None = None
    rated_at: str | None = None

    model_config = ConfigDict(extra='forbid')


class ActorFilmsPageResponse(BaseModel):
    items: list[ActorFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')
