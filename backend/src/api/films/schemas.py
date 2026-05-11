from __future__ import annotations

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
