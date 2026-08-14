from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class FilmAwardBadgeResponse(BaseModel):
    kind: Literal['oscar_best_picture_nominee', 'oscar_best_picture_winner']
    ceremony_year: int


class FilmResponse(BaseModel):
    id: int
    kinopoisk_id: int
    genres: list[str] = Field(default_factory=list)
    primary_director_kinopoisk_id: int | None = None
    primary_director_name: str | None = None
    primary_director_poster_url: str | None = None
    primary_director_tmdb_id: int | None = None
    imdb_id: str | None = None
    tmdb_id: int | None = None
    franchise_key: str | None = None
    franchise_label: str | None = None
    title: str
    year: int | None
    poster_url: str | None
    short_description: str | None = None
    description: str | None = None
    film_length: int | None = None
    slogan: str | None = None
    rating_kinopoisk: float | None = None
    rating_imdb: float | None = None
    rating_age_limits: str | None = None
    tmdb_recommendations: list[str] = Field(default_factory=list)
    trailer_youtube_url: str | None = None
    watch_providers_ru: list[str] = Field(default_factory=list)
    my_card_id: int | None = Field(
        default=None,
        description='Id карточки текущего пользователя для этого фильма, если уже оценивал',
    )
    award_badges: list[FilmAwardBadgeResponse] = Field(default_factory=list)


class FilmCommunityAuthorResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    display_name: str | None = None


class FilmCommunityCardItemResponse(BaseModel):
    id: int
    author: FilmCommunityAuthorResponse
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str = ''
    custom_tags: list[str] = Field(default_factory=list)
    updated_at: datetime
    is_favorite: bool = False


class FilmCommunityCardsPageResponse(BaseModel):
    items: list[FilmCommunityCardItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class FilmPlaybackResponse(BaseModel):
    provider: str
    title: str
    iframe_url: str
    film_id: int
    kinopoisk_id: int
    expires_at: datetime
