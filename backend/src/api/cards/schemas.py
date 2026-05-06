from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore


class CardCreateRequest(BaseModel):
    film_id: int = Field(..., ge=1)
    rating: float = Field(..., ge=1, le=10, multiple_of=0.5)
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str] = Field(default_factory=list, max_length=5)

    model_config = ConfigDict(extra='forbid')


class CardResponse(BaseModel):
    id: int
    film_id: int
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]


class CardDetailResponse(BaseModel):
    id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class FilmResolveResponse(BaseModel):
    id: int
    kinopoisk_id: int
    title: str
    year: int | None
    poster_url: str | None
