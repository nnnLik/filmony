from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedPostCreateRequest(BaseModel):
    body: str = Field(default='', max_length=2000)
    image_url: str | None = Field(default=None, max_length=2048)
    referenced_movie_card_id: int | None = Field(default=None, ge=1)
    source_comment_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')


class FeedPostImageUploadResponse(BaseModel):
    url: str


class FeedPostResponse(BaseModel):
    id: int
    user_id: UUID
    body: str
    image_url: str | None
    referenced_movie_card_id: int | None
    source_comment_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
