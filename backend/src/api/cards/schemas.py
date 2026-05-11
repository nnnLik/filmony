from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.reactions.schemas import ReactionSummaryResponse
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
    watch_note: str = Field(default='', max_length=500)

    model_config = ConfigDict(extra='forbid')


class CardResponse(BaseModel):
    id: int
    film_id: int
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]
    is_favorite: bool = False


class MovieCardCommentAuthorResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None


class CardDetailResponse(BaseModel):
    id: int
    user_id: UUID
    card_author: MovieCardCommentAuthorResponse
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
    watch_note: str = ''
    is_favorite: bool = False
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)


class CardUpdateRequest(BaseModel):
    rating: float | None = Field(default=None, ge=1, le=10, multiple_of=0.5)
    company: CardCompany | None = None
    mood_before: CardMoodBefore | None = None
    mood_after: CardMoodAfter | None = None
    custom_tags: list[str] | None = Field(default=None, max_length=5)
    watch_note: str | None = Field(default=None, max_length=500)
    is_favorite: bool | None = None

    model_config = ConfigDict(extra='forbid')


class MovieCardCommentResponse(BaseModel):
    id: int
    movie_card_id: int
    parent_comment_id: int | None
    text: str
    created_at: datetime
    replies_count: int = 0
    total_descendants_count: int = 0
    author: MovieCardCommentAuthorResponse
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)


class MovieCardCommentListResponse(BaseModel):
    items: list[MovieCardCommentResponse]
    next_cursor: str | None = None


class MovieCardCommentCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=250)
    parent_comment_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


FeedCardSource = Literal[
    'subscriptions',
    'subscribers',
    'personal_affinity',
    'discovery',
    'feed_posts',
]


class MovieCardFeedItemResponse(CardDetailResponse):
    kind: Literal['movie_card'] = 'movie_card'
    feed_source: FeedCardSource
    comments_count: int
    comments_preview: list[MovieCardCommentResponse] = Field(default_factory=list)


class FeedPostReferencedCardResponse(BaseModel):
    movie_card_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float


class FeedPostFeedItemResponse(BaseModel):
    kind: Literal['feed_post'] = 'feed_post'
    id: int
    user_id: UUID
    author: MovieCardCommentAuthorResponse
    body: str
    image_url: str | None
    referenced_movie_card_id: int | None
    source_comment_id: int | None
    created_at: datetime
    feed_source: FeedCardSource
    referenced_card: FeedPostReferencedCardResponse | None = None


FeedPageItemResponse = MovieCardFeedItemResponse | FeedPostFeedItemResponse


class MovieCardFeedPageResponse(BaseModel):
    items: list[FeedPageItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class UserFeedPostsPageResponse(BaseModel):
    """Посты пользователя (вкладка «Посты» в профиле)."""

    items: list[FeedPostFeedItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class FilmResolveResponse(BaseModel):
    id: int
    kinopoisk_id: int
    genres: list[str] = Field(default_factory=list)
    title: str
    year: int | None
    poster_url: str | None


class ShareCardRequest(BaseModel):
    recipient_user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    share_comment: str = Field(default='', max_length=500)

    model_config = ConfigDict(extra='forbid')


class ShareCardResponse(BaseModel):
    queued: int


class FollowingRatingEntryResponse(BaseModel):
    user_id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    rating: float


class FollowingRatingsListResponse(BaseModel):
    viewer_rating: FollowingRatingEntryResponse | None = None
    items: list[FollowingRatingEntryResponse] = Field(default_factory=list)
