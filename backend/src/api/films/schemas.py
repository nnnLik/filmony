from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class FilmResponse(BaseModel):
    id: int
    kinopoisk_id: int
    genres: list[str] = Field(default_factory=list)
    title: str
    year: int | None
    poster_url: str | None
    short_description: str | None = None
    description: str | None = None
    my_card_id: int | None = Field(
        default=None,
        description='Id карточки текущего пользователя для этого фильма, если уже оценивал',
    )


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
