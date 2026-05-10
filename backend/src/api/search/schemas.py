from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchFilmItemResponse(BaseModel):
    id: int
    kinopoisk_id: int
    genres: list[str] = Field(default_factory=list)
    title: str
    year: int | None
    poster_url: str | None

    model_config = ConfigDict(from_attributes=True)


class SearchUserItemResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None
    display_name: str | None
    photo_url: str | None
    movie_cards_count: int = 0
    average_rating: float | None = None

    model_config = ConfigDict(from_attributes=True)


class SearchCatalogResponse(BaseModel):
    films: list[SearchFilmItemResponse] = Field(default_factory=list)
    users: list[SearchUserItemResponse] = Field(default_factory=list)


class SearchSuggestionsResponse(BaseModel):
    mutual_circle: list[SearchUserItemResponse] = Field(default_factory=list)
    popular_authors: list[SearchUserItemResponse] = Field(default_factory=list)
    random_with_cards: list[SearchUserItemResponse] = Field(default_factory=list)
