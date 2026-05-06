from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore


class CardCreateRequest(BaseModel):
    film_id: int = Field(..., ge=1)
    kinopoisk_id: int = Field(..., ge=1)
    genres: list[str] = Field(default_factory=list, max_length=20)
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
    film_kinopoisk_id: int
    film_genres: list[str] = Field(default_factory=list)
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]


class MovieCardCommentAuthorResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None


class MovieCardCommentResponse(BaseModel):
    id: int
    movie_card_id: int
    parent_comment_id: int | None
    text: str
    created_at: datetime
    replies_count: int = 0
    total_descendants_count: int = 0
    author: MovieCardCommentAuthorResponse


class MovieCardCommentListResponse(BaseModel):
    items: list[MovieCardCommentResponse]
    next_cursor: str | None = None


class MovieCardCommentCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100)
    parent_comment_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class FilmResolveResponse(BaseModel):
    id: int
    kinopoisk_id: int
    genres: list[str] = Field(default_factory=list)
    title: str
    year: int | None
    poster_url: str | None
