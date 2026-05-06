from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class FilmResponse(BaseModel):
    id: int
    kinopoisk_id: int
    title: str
    year: int | None
    poster_url: str | None
