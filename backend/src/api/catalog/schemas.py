from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from api.films.schemas import FilmResponse


class CatalogResolveRequest(BaseModel):
    provider: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


class CatalogResolveResponse(BaseModel):
    catalog_item_id: int
    provider: str
    external_id: str
    title: str
    cover_url: str | None = None
    summary: str | None = None
    film: FilmResponse
