from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FranchiseSummaryResponse(BaseModel):
    franchise_key: str
    label: str
    films_count: int
    avg_community_rating: float | None = None

    model_config = ConfigDict(extra='forbid')


class FranchiseFilmItemResponse(BaseModel):
    film_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str] = Field(default_factory=list)
    community_avg_rating: float | None
    ratings_count: int
    my_card_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class FranchiseFilmsPageResponse(BaseModel):
    items: list[FranchiseFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')


class RatedFranchiseItemResponse(BaseModel):
    franchise_key: str
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class RatedFranchisesListResponse(BaseModel):
    items: list[RatedFranchiseItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')
