from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.cards.schemas import (
    MovieCardCommentAuthorResponse,
    ReferencedInlineMovieCardSnippetResponse,
    ReferencedMentionSnippetResponse,
)
from api.reactions.schemas import ReactionSummaryResponse


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


class FeedPostCommentResponse(BaseModel):
    id: int
    feed_post_id: int
    parent_comment_id: int | None
    text: str
    created_at: datetime
    replies_count: int = 0
    total_descendants_count: int = 0
    author: MovieCardCommentAuthorResponse
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)
    referenced_movie_cards: list[ReferencedInlineMovieCardSnippetResponse] = Field(
        default_factory=list,
    )
    referenced_mentions: list[ReferencedMentionSnippetResponse] = Field(
        default_factory=list,
    )


class FeedPostCommentListResponse(BaseModel):
    items: list[FeedPostCommentResponse]
    next_cursor: str | None = None


class FeedPostCommentCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=250)
    parent_comment_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')
