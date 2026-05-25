from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.cards.schemas import UserCardCategorySnippet
from models.catalog_item import CatalogProvider
from models.user import User
from services.profile.get_user_card_stats import UserCardStats
from services.profile.get_user_profile_counts import UserProfileCounts
from services.profile.list_user_cards import UserCardListPage
from services.subscriptions.list_user_subscriptions import (
    SubscriptionListItem,
)
from services.watchlist.list_user_watchlist_films import WatchlistFilmPage


class MyUserCardCategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(extra='forbid')


class MyUserCardCategoryListResponse(BaseModel):
    items: list[MyUserCardCategoryResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class MyUserCardCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)

    model_config = ConfigDict(extra='forbid')


class MyUserCardCategoryRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)

    model_config = ConfigDict(extra='forbid')


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra='forbid')


class MyProfileResponse(BaseModel):
    id: UUID
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    language_code: str | None
    profile_slug: str
    display_name: str | None
    bio: str | None
    cards_count: int = 0
    favorites_count: int = 0
    watchlist_count: int = 0
    friends_count: int = 0
    followers_count: int = 0
    following_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserCardsExportCsvResponse(BaseModel):
    status: str = Field(examples=['sent'])


class MyUserCardTagStatItem(BaseModel):
    tag: str
    use_count: int = Field(..., ge=1)

    model_config = ConfigDict(extra='forbid')


class MyUserCardTagStatsResponse(BaseModel):
    items: list[MyUserCardTagStatItem] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class PublicProfileResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    bio: str | None
    cards_count: int = 0
    favorites_count: int = 0
    watchlist_count: int = 0
    friends_count: int = 0
    followers_count: int = 0
    following_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserCardItemResponse(BaseModel):
    id: int
    film_id: int | None = None
    film_kinopoisk_id: int | None = None
    film_genres: list[str] = Field(default_factory=list)
    film_title: str
    film_year: int | None
    release_year: int | None = None
    release_date: str | None = None
    film_poster_url: str | None
    catalog_item_id: int | None = None
    provider: CatalogProvider
    external_id: str | None = None
    display_title: str
    display_cover_url: str | None = None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str] = Field(default_factory=list)
    watch_note: str = ''
    category: UserCardCategorySnippet
    is_favorite: bool = False
    audio_url: str | None = None


class UserCardPageResponse(BaseModel):
    items: list[UserCardItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class WatchlistFilmItemResponse(BaseModel):
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str] = Field(default_factory=list)
    film_title: str
    film_year: int | None
    film_poster_url: str | None


class WatchlistFilmPageResponse(BaseModel):
    items: list[WatchlistFilmItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


class WatchlistMembershipResponse(BaseModel):
    in_watchlist: bool


class WatchlistFilmAddRequest(BaseModel):
    film_id: int = Field(..., ge=1)

    model_config = ConfigDict(extra='forbid')


class SubscriptionListItemResponse(BaseModel):
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    relation_type: str


class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionListItemResponse] = Field(default_factory=list)


class RatingDistributionItemResponse(BaseModel):
    rating: int
    count: int


class YearDistributionItemResponse(BaseModel):
    year: int
    count: int


class ValueDistributionItemResponse(BaseModel):
    value: str
    count: int


class TagDistributionItemResponse(BaseModel):
    tag: str
    count: int


class CategoryDistributionItemResponse(BaseModel):
    category_id: int | None
    name: str
    count: int

    model_config = ConfigDict(extra='forbid')


class ProfileStatsMovieItemResponse(BaseModel):
    card_id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float


class UserCardStatsApiResponse(BaseModel):
    total_movies: int
    average_rating: float
    rating_distribution: list[RatingDistributionItemResponse] = Field(default_factory=list)
    year_distribution: list[YearDistributionItemResponse] = Field(default_factory=list)
    popular_tags: list[TagDistributionItemResponse] = Field(default_factory=list)
    watch_with_distribution: list[ValueDistributionItemResponse] = Field(default_factory=list)
    mood_after_distribution: list[ValueDistributionItemResponse] = Field(default_factory=list)
    category_distribution: list[CategoryDistributionItemResponse] = Field(default_factory=list)
    top_movies: list[ProfileStatsMovieItemResponse] = Field(default_factory=list)
    worst_movies: list[ProfileStatsMovieItemResponse] = Field(default_factory=list)


def build_my_profile_response(user: User, counts: UserProfileCounts) -> MyProfileResponse:
    return MyProfileResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        photo_url=user.photo_url,
        language_code=user.language_code,
        profile_slug=user.profile_slug,
        display_name=user.display_name,
        bio=user.bio,
        cards_count=counts.movie_cards,
        favorites_count=counts.favorites,
        watchlist_count=counts.watchlist_films,
        friends_count=counts.friends,
        followers_count=counts.followers_count,
        following_count=counts.following_count,
    )


def build_public_profile_response(user: User, counts: UserProfileCounts) -> PublicProfileResponse:
    return PublicProfileResponse(
        id=user.id,
        profile_slug=user.profile_slug,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        photo_url=user.photo_url,
        display_name=user.display_name,
        bio=user.bio,
        cards_count=counts.movie_cards,
        favorites_count=counts.favorites,
        watchlist_count=counts.watchlist_films,
        friends_count=counts.friends,
        followers_count=counts.followers_count,
        following_count=counts.following_count,
    )


def build_user_card_page_response(page: UserCardListPage) -> UserCardPageResponse:
    items = [
        UserCardItemResponse(
            id=item.id,
            film_id=item.film_id,
            film_kinopoisk_id=item.film_kinopoisk_id,
            film_genres=item.film_genres,
            film_title=item.film_title,
            film_year=item.film_year,
            release_year=item.release_year,
            release_date=item.release_date,
            film_poster_url=item.film_poster_url,
            catalog_item_id=item.catalog_item_id,
            provider=item.provider,
            external_id=item.external_id,
            display_title=item.display_title,
            display_cover_url=item.display_cover_url,
            rating=item.rating,
            company=item.company,
            mood_before=item.mood_before,
            mood_after=item.mood_after,
            custom_tags=item.custom_tags,
            watch_note=item.watch_note,
            category=UserCardCategorySnippet(id=item.category_id, name=item.category_name),
            is_favorite=item.is_favorite,
            audio_url=item.audio_url,
        )
        for item in page.items
    ]
    return UserCardPageResponse(items=items, next_cursor=page.next_cursor)


def build_watchlist_film_page_response(page: WatchlistFilmPage) -> WatchlistFilmPageResponse:
    items = [
        WatchlistFilmItemResponse(
            film_id=item.film_id,
            film_kinopoisk_id=item.film_kinopoisk_id,
            film_genres=item.film_genres,
            film_title=item.film_title,
            film_year=item.film_year,
            film_poster_url=item.film_poster_url,
        )
        for item in page.items
    ]
    return WatchlistFilmPageResponse(items=items, next_cursor=page.next_cursor)


def build_subscription_list_response(items: list[SubscriptionListItem]) -> SubscriptionListResponse:
    return SubscriptionListResponse(
        items=[
            SubscriptionListItemResponse(
                id=item.id,
                profile_slug=item.profile_slug,
                username=item.username,
                first_name=item.first_name,
                last_name=item.last_name,
                photo_url=item.photo_url,
                display_name=item.display_name,
                relation_type=item.relation_type.value,
            )
            for item in items
        ]
    )


def build_user_card_stats_response(stats: UserCardStats) -> UserCardStatsApiResponse:
    return UserCardStatsApiResponse(
        total_movies=stats.total_movies,
        average_rating=stats.average_rating,
        rating_distribution=[
            RatingDistributionItemResponse(rating=item.rating, count=item.count)
            for item in stats.rating_distribution
        ],
        year_distribution=[
            YearDistributionItemResponse(year=item.year, count=item.count)
            for item in stats.year_distribution
        ],
        popular_tags=[
            TagDistributionItemResponse(tag=item.tag, count=item.count)
            for item in stats.popular_tags
        ],
        watch_with_distribution=[
            ValueDistributionItemResponse(value=item.value, count=item.count)
            for item in stats.watch_with_distribution
        ],
        mood_after_distribution=[
            ValueDistributionItemResponse(value=item.value, count=item.count)
            for item in stats.mood_after_distribution
        ],
        category_distribution=[
            CategoryDistributionItemResponse(
                category_id=item.category_id,
                name=item.name,
                count=item.count,
            )
            for item in stats.category_distribution
        ],
        top_movies=[
            ProfileStatsMovieItemResponse(
                card_id=item.card_id,
                film_id=item.film_id,
                film_title=item.film_title,
                film_year=item.film_year,
                film_poster_url=item.film_poster_url,
                rating=item.rating,
            )
            for item in stats.top_movies
        ],
        worst_movies=[
            ProfileStatsMovieItemResponse(
                card_id=item.card_id,
                film_id=item.film_id,
                film_title=item.film_title,
                film_year=item.film_year,
                film_poster_url=item.film_poster_url,
                rating=item.rating,
            )
            for item in stats.worst_movies
        ],
    )
