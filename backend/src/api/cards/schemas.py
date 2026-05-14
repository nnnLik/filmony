from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.reactions.schemas import ReactionSummaryResponse
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogProvider


class UserCardCategorySnippet(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(extra='forbid')


class CardCreateRequest(BaseModel):
    """Create a card: film-backed, ``catalog_item_id``, Kinopoisk ``provider`` + ``external_id``, or manual."""

    film_id: int | None = Field(default=None, ge=1)
    kinopoisk_id: int | None = Field(default=None, ge=1)
    catalog_item_id: int | None = Field(default=None, ge=1)
    provider: CatalogProvider | None = None
    external_id: str | None = Field(default=None, max_length=255)
    display_title: str | None = Field(default=None, max_length=255)
    display_cover_url: str | None = Field(default=None, max_length=2048)
    display_summary: str | None = None
    genres: list[str] = Field(default_factory=list, max_length=20)
    rating: float = Field(..., ge=1, le=10, multiple_of=0.5)
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str] = Field(default_factory=list, max_length=5)
    watch_note: str = Field(default='', max_length=500)
    category_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def validate_create_mode(self) -> CardCreateRequest:
        ext_norm = (self.external_id or '').strip() or None

        has_film = self.film_id is not None
        has_catalog = self.catalog_item_id is not None
        title = (self.display_title or '').strip()

        has_ke = self.provider == CatalogProvider.kinopoisk and ext_norm is not None

        if self.provider == CatalogProvider.no_provider:
            if ext_norm is not None:
                raise ValueError('external_id must not be set for no_provider')
            if has_film or has_catalog or has_ke:
                raise ValueError(
                    'no_provider cannot be combined with film_id, catalog_item_id, '
                    'or kinopoisk external_id',
                )
            if not title:
                raise ValueError('display_title is required for no_provider')

        if (
            self.provider == CatalogProvider.kinopoisk
            and not has_ke
            and not has_film
            and not has_catalog
        ):
            raise ValueError(
                'provider kinopoisk requires external_id, '
                'or omit provider and use film_id/catalog_item_id',
            )

        if ext_norm is not None:
            if self.provider not in (None, CatalogProvider.kinopoisk):
                raise ValueError('external_id is only valid with provider kinopoisk')
            if self.provider is None:
                raise ValueError('provider kinopoisk is required when external_id is set')

        is_manual = not has_film and not has_catalog and not has_ke and bool(title)

        modes = int(has_film) + int(has_catalog) + int(has_ke) + int(is_manual)
        if modes != 1:
            raise ValueError(
                'exactly one of film_id (with kinopoisk_id), catalog_item_id, '
                'kinopoisk external subject (provider kinopoisk + external_id), '
                'or non-empty display_title (manual card) must be provided',
            )

        if has_film and self.kinopoisk_id is None:
            raise ValueError('kinopoisk_id is required when film_id is set')
        return self


class CardResponse(BaseModel):
    id: int
    film_id: int | None = None
    catalog_item_id: int | None = None
    provider: CatalogProvider
    external_id: str | None = None
    display_title: str
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]
    category: UserCardCategorySnippet
    is_favorite: bool = False


class ReferencedInlineMovieCardSnippetResponse(BaseModel):
    movie_card_id: int
    film_title: str
    film_year: int | None = None


class ReferencedMentionSnippetResponse(BaseModel):
    """Подписи для токенов ⟦@slug⟧ (slug в нижнем регистре, как в тексте)."""

    user_id: UUID
    profile_slug: str
    display_label: str
    username: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class WatchedInlinePickerRowResponse(BaseModel):
    movie_card_id: int
    film_title: str
    film_year: int | None = None


class WatchedInlinePickerListResponse(BaseModel):
    items: list[WatchedInlinePickerRowResponse] = Field(default_factory=list)


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
    film_id: int | None = None
    film_kinopoisk_id: int | None = None
    film_genres: list[str] = Field(default_factory=list)
    film_title: str
    film_year: int | None
    release_year: int | None = None
    release_date: str | None = Field(
        default=None,
        description='ISO date YYYY-MM-DD when known (typically RAWG games)',
    )
    film_poster_url: str | None
    catalog_item_id: int | None = None
    provider: CatalogProvider
    external_id: str | None = None
    display_title: str
    display_cover_url: str | None = None
    display_summary: str | None = None
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: list[str]
    watch_note: str = ''
    category: UserCardCategorySnippet
    is_favorite: bool = False
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)


class MovieCardDetailResponse(CardDetailResponse):
    """Полная карточка (GET /cards/:id): синопсис из БД, не отдаётся в ленте."""

    film_short_description: str | None = None
    film_description: str | None = None


class CardUpdateRequest(BaseModel):
    rating: float | None = Field(default=None, ge=1, le=10, multiple_of=0.5)
    company: CardCompany | None = None
    mood_before: CardMoodBefore | None = None
    mood_after: CardMoodAfter | None = None
    custom_tags: list[str] | None = Field(default=None, max_length=5)
    watch_note: str | None = Field(default=None, max_length=500)
    is_favorite: bool | None = None
    category_id: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra='forbid')


class MovieCardCommentResponse(BaseModel):
    id: int
    movie_card_id: int
    parent_comment_id: int | None
    text: str
    image_url: str | None = None
    created_at: datetime
    replies_count: int = 0
    total_descendants_count: int = 0
    author: MovieCardCommentAuthorResponse
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)
    referenced_movie_cards: list[ReferencedInlineMovieCardSnippetResponse] = Field(
        default_factory=list,
        description='Сниппеты фильмов для токенов ⟦c{id}⟧ в тексте (порядок первых вхождений id)',
    )
    referenced_mentions: list[ReferencedMentionSnippetResponse] = Field(
        default_factory=list,
        description='Профили для токенов ⟦@slug⟧ (порядок первых вхождений slug)',
    )


class MovieCardCommentListResponse(BaseModel):
    items: list[MovieCardCommentResponse]
    next_cursor: str | None = None


class MovieCardCommentCreateRequest(BaseModel):
    text: str = Field(default='', max_length=250)
    parent_comment_id: int | None = Field(default=None, ge=1)
    image_url: str | None = Field(default=None, max_length=2048)

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def require_text_or_image(self) -> MovieCardCommentCreateRequest:
        if self.text.strip() == '' and (
            self.image_url is None or str(self.image_url).strip() == ''
        ):
            raise ValueError('text or image_url is required')
        return self


class FilmResolveRequest(BaseModel):
    url: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')


FeedCardSource = Literal[
    'subscriptions',
    'subscribers',
    'personal_affinity',
    'discovery',
    'feed_posts',
    'own_cards',
    'global',
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
    release_year: int | None = None
    release_date: str | None = None
    film_poster_url: str | None
    rating: float


class FeedPostCommentPreviewResponse(BaseModel):
    """Превью комментария к посту в ленте (без циклического импорта с `api.feed_posts.schemas`)."""

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


class FeedPostSourceCommentSnippetResponse(BaseModel):
    id: int
    text: str
    image_url: str | None = None
    author: MovieCardCommentAuthorResponse
    referenced_movie_cards: list[ReferencedInlineMovieCardSnippetResponse] = Field(
        default_factory=list,
    )
    referenced_mentions: list[ReferencedMentionSnippetResponse] = Field(default_factory=list)


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
    reactions: ReactionSummaryResponse = Field(default_factory=ReactionSummaryResponse)
    comments_count: int = 0
    comments_preview: list[FeedPostCommentPreviewResponse] = Field(default_factory=list)
    body_referenced_movie_cards: list[ReferencedInlineMovieCardSnippetResponse] = Field(
        default_factory=list,
    )
    body_referenced_mentions: list[ReferencedMentionSnippetResponse] = Field(
        default_factory=list,
    )
    source_comment: FeedPostSourceCommentSnippetResponse | None = None


FeedPageItemResponse = MovieCardFeedItemResponse | FeedPostFeedItemResponse


class MovieCardFeedPageResponse(BaseModel):
    items: list[FeedPageItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None
    feed_head_version: int = Field(
        default=0,
        description='Монотонная версия «головы» глобальной ленты (для SSE/клиента); 0 если не применимо',
    )


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
    short_description: str | None = None
    description: str | None = None


class ShareCardRequest(BaseModel):
    recipient_user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    share_comment: str = Field(default='', max_length=500)

    model_config = ConfigDict(extra='forbid')


class ShareCardResponse(BaseModel):
    queued: int


class FollowingRatingEntryResponse(BaseModel):
    user_id: UUID
    movie_card_id: int
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
