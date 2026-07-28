from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class WeeklyControversyItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anchor_film_id: int | None = None
    anchor_catalog_item_id: int | None = None
    title: str
    spread: float = Field(ge=0)
    rater_count: int = Field(ge=3)
    min_rating: float = Field(ge=1)
    max_rating: float = Field(ge=1)


class WeeklyControversyResponse(BaseModel):
    week_start: dt.date
    controversy: WeeklyControversyItemResponse | None = None
