from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.achievements.schemas import PinnedAchievementResponse, build_pinned_achievement_response
from api.cards.schemas import UserCardCategorySnippet
from api.watchlist.schemas import WatchTag
from models.card_enums import CardCompany
from models.catalog_item import CatalogProvider
from models.user import User
from services.achievements.list_pinned_achievements import PinnedAchievementDTO
from services.profile.get_user_card_stats import UserCardStats
from services.profile.get_user_profile_counts import UserProfileCounts
from services.profile.get_user_profile_social_insights import UserProfileSocialInsights
from services.profile.list_user_cards import UserCardListPage
from services.subscriptions.list_user_subscriptions import (
    SubscriptionListItem,
)
from services.watchlist.list_user_watchlist_entries import (
    WatchlistEntryListItem,
    WatchlistEntryPage,
)
from services.watchlist.list_watchlist_overlaps import (
    WatchlistOverlapItem,
    WatchlistOverlapPage,
    WatchlistOverlapPartner,
)
from services.watchlist.pick_evening_for_two_film import EveningForTwoPick


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


class WatchlistFilmCreateRequest(BaseModel):
    film_id: int | None = Field(default=None, ge=1)
    catalog_item_id: int | None = Field(default=None, ge=1)
    card_id: str | None = Field(default=None, min_length=1, max_length=128)
    provider_meta: dict | None = None
    watch_tag: WatchTag = WatchTag.watch_later
    company: CardCompany = CardCompany.alone
    category_id: int | None = Field(default=None, ge=1)
    watch_note: str = Field(default='')
    watch_with_user_id: UUID | None = None
    watch_with_user_ids: list[UUID] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra='forbid')

    @field_validator('watch_with_user_ids')
    @classmethod
    def _validate_partner_count(cls, value: list[UUID]) -> list[UUID]:
        if len(value) > 20:
            raise ValueError('max 20 watch partners allowed')
        return value


class WatchlistEntryUpdateRequest(BaseModel):
    company: CardCompany = CardCompany.alone
    category_id: int | None = Field(default=None, ge=1)
    watch_note: str = Field(default='')
    watch_with_user_id: UUID | None = None
    watch_with_user_ids: list[UUID] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(extra='forbid')

    @field_validator('watch_with_user_ids')
    @classmethod
    def _validate_partner_count(cls, value: list[UUID]) -> list[UUID]:
        if len(value) > 20:
            raise ValueError('max 20 watch partners allowed')
        return value


class PlannedUserCardResponse(BaseModel):
    user_card_id: int
    company: CardCompany
    category_id: int
    watch_note: str

    model_config = ConfigDict(extra='forbid')


class WatchlistEntryItemResponse(BaseModel):
    entry_id: int
    card_id: str
    provider: str
    title: str
    poster_url: str | None
    year: int | None
    watch_tag: str
    watch_with_user_id: UUID | None
    watch_with_user_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    film_id: int | None = None
    film_kinopoisk_id: int | None = None
    film_genres: list[str] = Field(default_factory=list)
    catalog_item_id: int | None = None
    external_id: str | None = None
    planned_user_card_id: int | None = None
    # Legacy aliases for Kinopoisk clients
    film_title: str | None = None
    film_year: int | None = None
    film_poster_url: str | None = None

    model_config = ConfigDict(extra='forbid')


class WatchlistEntryPageResponse(BaseModel):
    items: list[WatchlistEntryItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None

    model_config = ConfigDict(extra='forbid')


class WatchlistMembershipResponse(BaseModel):
    in_watchlist: bool

    model_config = ConfigDict(extra='forbid')


class WatchlistOverlapPartnerResponse(BaseModel):
    user_id: UUID
    slug: str
    display_name: str | None
    avatar_url: str | None

    model_config = ConfigDict(extra='forbid')


class WatchlistOverlapItemResponse(BaseModel):
    entry_id: int
    title: str
    poster_url: str | None
    card_id: str
    film_id: int | None = None
    catalog_item_id: int | None = None
    watch_with_user_ids: list[UUID] = Field(default_factory=list)
    company: str = 'alone'
    watch_note: str = ''
    partners: list[WatchlistOverlapPartnerResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class WatchlistOverlapListResponse(BaseModel):
    items: list[WatchlistOverlapItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class EveningForTwoPickResponse(BaseModel):
    entry_id: int
    film_id: int
    title: str
    poster_url: str | None
    partner: WatchlistOverlapPartnerResponse

    model_config = ConfigDict(extra='forbid')


class WatchlistFilmItemResponse(BaseModel):
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str] = Field(default_factory=list)
    film_primary_director_kinopoisk_id: int | None = None
    film_primary_director_name: str | None = None
    film_title: str
    film_year: int | None
    film_poster_url: str | None

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
    pinned_achievements: list[PinnedAchievementResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserCardItemResponse(BaseModel):
    id: int
    film_id: int | None = None
    film_kinopoisk_id: int | None = None
    film_genres: list[str] = Field(default_factory=list)
    film_primary_director_kinopoisk_id: int | None = None
    film_primary_director_name: str | None = None
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
    community_avg_rating: float | None = None
    is_contrarian: bool = False


class UserCardPageResponse(BaseModel):
    items: list[UserCardItemResponse] = Field(default_factory=list)
    next_cursor: str | None = None


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


class TagTasteItemResponse(BaseModel):
    tag: str
    count: int
    average_rating: float

    model_config = ConfigDict(extra='forbid')


class ProfileInsightsResponse(BaseModel):
    activity_total_180d: int
    dominant_company: str | None
    dominant_mood_after: str | None
    top_tag: str | None
    top_director_kinopoisk_id: int | None = None
    top_director_name: str | None = None
    top_director_count: int = 0
    top_actor_kinopoisk_id: int | None = None
    top_actor_name: str | None = None
    top_actor_count: int = 0
    top_franchise_key: str | None = None
    top_franchise_label: str | None = None
    top_franchise_count: int = 0

    model_config = ConfigDict(extra='forbid')


class TasteMatchBreakdownResponse(BaseModel):
    shared_titles: float
    tag_overlap: float
    rating_agreement: float
    shared_favorites: float

    model_config = ConfigDict(extra='forbid')


class TastePeerItemResponse(BaseModel):
    id: UUID
    profile_slug: str
    display_name: str | None
    photo_url: str | None
    similarity_score: float
    shared_films_count: int
    score_v2: float
    breakdown: TasteMatchBreakdownResponse

    model_config = ConfigDict(extra='forbid')


class ProfileSocialInsightsResponse(BaseModel):
    mutual_subscriptions_count: int
    taste_peers: list[TastePeerItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class CategoryDistributionItemResponse(BaseModel):
    category_id: int | None
    name: str
    count: int

    model_config = ConfigDict(extra='forbid')


class GenreDistributionItemResponse(BaseModel):
    genre: str
    count: int

    model_config = ConfigDict(extra='forbid')


class DirectorDistributionItemResponse(BaseModel):
    kinopoisk_id: int
    name: str
    poster_url: str | None = None
    count: int

    model_config = ConfigDict(extra='forbid')


class ActorDistributionItemResponse(BaseModel):
    kinopoisk_id: int
    name: str
    poster_url: str | None = None
    count: int

    model_config = ConfigDict(extra='forbid')


class FranchiseDistributionItemResponse(BaseModel):
    franchise_key: str
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class ActivityDistributionItemResponse(BaseModel):
    date: date
    count: int

    model_config = ConfigDict(extra='forbid')


class ProfileStatsMovieItemResponse(BaseModel):
    card_id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float


class RatingContrastOutlierResponse(BaseModel):
    card_id: int
    film_id: int
    film_title: str
    user_rating: float
    external_rating: float
    delta: float

    model_config = ConfigDict(extra='forbid')


class RatingContrastInsightsResponse(BaseModel):
    kinopoisk_compared_count: int
    kinopoisk_higher_count: int
    kinopoisk_lower_count: int
    kinopoisk_biggest_positive: RatingContrastOutlierResponse | None = None
    kinopoisk_biggest_negative: RatingContrastOutlierResponse | None = None
    imdb_compared_count: int
    imdb_higher_count: int
    imdb_lower_count: int
    imdb_biggest_positive: RatingContrastOutlierResponse | None = None
    imdb_biggest_negative: RatingContrastOutlierResponse | None = None

    model_config = ConfigDict(extra='forbid')


class UserCardStatsApiResponse(BaseModel):
    total_movies: int
    average_rating: float
    rating_distribution: list[RatingDistributionItemResponse] = Field(default_factory=list)
    year_distribution: list[YearDistributionItemResponse] = Field(default_factory=list)
    rated_year_distribution: list[YearDistributionItemResponse] = Field(default_factory=list)
    popular_tags: list[TagDistributionItemResponse] = Field(default_factory=list)
    tag_taste: list[TagTasteItemResponse] = Field(default_factory=list)
    insights: ProfileInsightsResponse
    watch_with_distribution: list[ValueDistributionItemResponse] = Field(default_factory=list)
    mood_after_distribution: list[ValueDistributionItemResponse] = Field(default_factory=list)
    category_distribution: list[CategoryDistributionItemResponse] = Field(default_factory=list)
    genre_distribution: list[GenreDistributionItemResponse] = Field(default_factory=list)
    director_distribution: list[DirectorDistributionItemResponse] = Field(default_factory=list)
    actor_distribution: list[ActorDistributionItemResponse] = Field(default_factory=list)
    franchise_distribution: list[FranchiseDistributionItemResponse] = Field(default_factory=list)
    top_movies: list[ProfileStatsMovieItemResponse] = Field(default_factory=list)
    worst_movies: list[ProfileStatsMovieItemResponse] = Field(default_factory=list)
    activity_distribution: list[ActivityDistributionItemResponse] = Field(default_factory=list)
    activity_start: date
    activity_end: date
    rating_contrast: RatingContrastInsightsResponse
    social: ProfileSocialInsightsResponse


def build_watchlist_entry_item_response(item: WatchlistEntryListItem) -> WatchlistEntryItemResponse:
    return WatchlistEntryItemResponse(
        entry_id=item.entry_id,
        card_id=item.card_id,
        provider=item.provider,
        title=item.title,
        poster_url=item.poster_url,
        year=item.year,
        watch_tag=item.watch_tag,
        watch_with_user_id=item.watch_with_user_id,
        watch_with_user_ids=list(item.watch_with_user_ids or []),
        created_at=item.created_at,
        film_id=item.film_id,
        film_kinopoisk_id=item.film_kinopoisk_id,
        film_genres=list(item.film_genres or []),
        catalog_item_id=item.catalog_item_id,
        external_id=item.external_id,
        planned_user_card_id=item.planned_user_card_id,
        film_title=item.title if item.provider == 'kinopoisk' else None,
        film_year=item.year if item.provider == 'kinopoisk' else None,
        film_poster_url=item.poster_url if item.provider == 'kinopoisk' else None,
    )


def build_watchlist_entry_page_response(page: WatchlistEntryPage) -> WatchlistEntryPageResponse:
    return WatchlistEntryPageResponse(
        items=[build_watchlist_entry_item_response(it) for it in page.items],
        next_cursor=page.next_cursor,
    )


def build_watchlist_overlap_partner_response(
    partner: WatchlistOverlapPartner,
) -> WatchlistOverlapPartnerResponse:
    return WatchlistOverlapPartnerResponse(
        user_id=partner.user_id,
        slug=partner.slug,
        display_name=partner.display_name,
        avatar_url=partner.avatar_url,
    )


def build_watchlist_overlap_item_response(
    item: WatchlistOverlapItem,
) -> WatchlistOverlapItemResponse:
    return WatchlistOverlapItemResponse(
        entry_id=item.entry_id,
        title=item.title,
        poster_url=item.poster_url,
        card_id=item.card_id,
        film_id=item.film_id,
        catalog_item_id=item.catalog_item_id,
        watch_with_user_ids=list(item.watch_with_user_ids),
        company=item.company,
        watch_note=item.watch_note,
        partners=[build_watchlist_overlap_partner_response(p) for p in item.partners],
    )


def build_watchlist_overlap_list_response(
    page: WatchlistOverlapPage,
) -> WatchlistOverlapListResponse:
    return WatchlistOverlapListResponse(
        items=[build_watchlist_overlap_item_response(it) for it in page.items],
    )


def build_evening_for_two_pick_response(pick: EveningForTwoPick) -> EveningForTwoPickResponse:
    return EveningForTwoPickResponse(
        entry_id=pick.entry_id,
        film_id=pick.film_id,
        title=pick.title,
        poster_url=pick.poster_url,
        partner=build_watchlist_overlap_partner_response(pick.partner),
    )


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


def build_public_profile_response(
    user: User,
    counts: UserProfileCounts,
    *,
    pinned_achievements: list[PinnedAchievementDTO] | None = None,
) -> PublicProfileResponse:
    pinned = pinned_achievements or []
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
        pinned_achievements=[build_pinned_achievement_response(item) for item in pinned],
    )


def build_user_card_page_response(
    page: UserCardListPage,
    *,
    community_by_card_id: dict[int, tuple[float | None, bool]] | None = None,
) -> UserCardPageResponse:
    community = community_by_card_id or {}
    items = []
    for item in page.items:
        avg, contrarian = community.get(item.id, (None, False))
        items.append(
            UserCardItemResponse(
                id=item.id,
                film_id=item.film_id,
                film_kinopoisk_id=item.film_kinopoisk_id,
                film_genres=item.film_genres,
                film_primary_director_kinopoisk_id=item.film_primary_director_kinopoisk_id,
                film_primary_director_name=item.film_primary_director_name,
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
                community_avg_rating=avg,
                is_contrarian=contrarian,
            )
        )
    return UserCardPageResponse(items=items, next_cursor=page.next_cursor)


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


def _rating_contrast_outlier_response(outlier) -> RatingContrastOutlierResponse | None:
    if outlier is None:
        return None
    return RatingContrastOutlierResponse(
        card_id=outlier.card_id,
        film_id=outlier.film_id,
        film_title=outlier.film_title,
        user_rating=outlier.user_rating,
        external_rating=outlier.external_rating,
        delta=outlier.delta,
    )


def build_user_card_stats_response(
    stats: UserCardStats,
    *,
    social: UserProfileSocialInsights,
) -> UserCardStatsApiResponse:
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
        rated_year_distribution=[
            YearDistributionItemResponse(year=item.year, count=item.count)
            for item in stats.rated_year_distribution
        ],
        popular_tags=[
            TagDistributionItemResponse(tag=item.tag, count=item.count)
            for item in stats.popular_tags
        ],
        tag_taste=[
            TagTasteItemResponse(
                tag=item.tag,
                count=item.count,
                average_rating=item.average_rating,
            )
            for item in stats.tag_taste
        ],
        insights=ProfileInsightsResponse(
            activity_total_180d=stats.insights.activity_total_180d,
            dominant_company=stats.insights.dominant_company,
            dominant_mood_after=stats.insights.dominant_mood_after,
            top_tag=stats.insights.top_tag,
            top_director_kinopoisk_id=stats.insights.top_director_kinopoisk_id,
            top_director_name=stats.insights.top_director_name,
            top_director_count=stats.insights.top_director_count,
            top_actor_kinopoisk_id=stats.insights.top_actor_kinopoisk_id,
            top_actor_name=stats.insights.top_actor_name,
            top_actor_count=stats.insights.top_actor_count,
            top_franchise_key=stats.insights.top_franchise_key,
            top_franchise_label=stats.insights.top_franchise_label,
            top_franchise_count=stats.insights.top_franchise_count,
        ),
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
        genre_distribution=[
            GenreDistributionItemResponse(genre=item.genre, count=item.count)
            for item in stats.genre_distribution
        ],
        director_distribution=[
            DirectorDistributionItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                name=item.name,
                poster_url=item.poster_url,
                count=item.count,
            )
            for item in stats.director_distribution
        ],
        actor_distribution=[
            ActorDistributionItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                name=item.name,
                poster_url=item.poster_url,
                count=item.count,
            )
            for item in stats.actor_distribution
        ],
        franchise_distribution=[
            FranchiseDistributionItemResponse(
                franchise_key=item.franchise_key,
                label=item.label,
                count=item.count,
            )
            for item in stats.franchise_distribution
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
        activity_distribution=[
            ActivityDistributionItemResponse(date=item.date, count=item.count)
            for item in stats.activity_distribution
        ],
        activity_start=stats.activity_start,
        activity_end=stats.activity_end,
        rating_contrast=RatingContrastInsightsResponse(
            kinopoisk_compared_count=stats.rating_contrast.kinopoisk_compared_count,
            kinopoisk_higher_count=stats.rating_contrast.kinopoisk_higher_count,
            kinopoisk_lower_count=stats.rating_contrast.kinopoisk_lower_count,
            kinopoisk_biggest_positive=_rating_contrast_outlier_response(
                stats.rating_contrast.kinopoisk_biggest_positive,
            ),
            kinopoisk_biggest_negative=_rating_contrast_outlier_response(
                stats.rating_contrast.kinopoisk_biggest_negative,
            ),
            imdb_compared_count=stats.rating_contrast.imdb_compared_count,
            imdb_higher_count=stats.rating_contrast.imdb_higher_count,
            imdb_lower_count=stats.rating_contrast.imdb_lower_count,
            imdb_biggest_positive=_rating_contrast_outlier_response(
                stats.rating_contrast.imdb_biggest_positive,
            ),
            imdb_biggest_negative=_rating_contrast_outlier_response(
                stats.rating_contrast.imdb_biggest_negative,
            ),
        ),
        social=ProfileSocialInsightsResponse(
            mutual_subscriptions_count=social.mutual_subscriptions_count,
            taste_peers=[
                TastePeerItemResponse(
                    id=peer.id,
                    profile_slug=peer.profile_slug,
                    display_name=peer.display_name,
                    photo_url=peer.photo_url,
                    similarity_score=peer.similarity_score,
                    shared_films_count=peer.shared_films_count,
                    score_v2=peer.score_v2,
                    breakdown=TasteMatchBreakdownResponse(
                        shared_titles=peer.breakdown.shared_titles,
                        tag_overlap=peer.breakdown.tag_overlap,
                        rating_agreement=peer.breakdown.rating_agreement,
                        shared_favorites=peer.breakdown.shared_favorites,
                    ),
                )
                for peer in social.taste_peers
            ],
        ),
    )


class MonthlyRecapTopFilmResponse(BaseModel):
    card_id: int
    film_id: int | None
    title: str
    poster_url: str | None
    rating: float

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapStampResponse(BaseModel):
    stamp_id: str
    title: str
    unlocked_at: datetime

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapMarathonResponse(BaseModel):
    kind: str
    key: str
    label: str
    unlocked_at: datetime

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapDistributionItemResponse(BaseModel):
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapDecadeItemResponse(BaseModel):
    decade_start: int
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapDirectorItemResponse(BaseModel):
    kinopoisk_id: int
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapFranchiseItemResponse(BaseModel):
    franchise_key: str
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapActorItemResponse(BaseModel):
    kinopoisk_id: int
    label: str
    count: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapCollectionDeltaItemResponse(BaseModel):
    collection_slug: str
    title: str
    films_rated_in_period: int

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapAchievementItemResponse(BaseModel):
    slug: str
    title: str
    rarity_percent: float | None = None

    model_config = ConfigDict(extra='forbid')


class MonthlyRecapResponse(BaseModel):
    year: int
    month: int
    month_label: str
    total_rated: int
    average_rating: float
    top_films: list[MonthlyRecapTopFilmResponse] = Field(default_factory=list)
    new_stamps: list[MonthlyRecapStampResponse] = Field(default_factory=list)
    marathons_unlocked: list[MonthlyRecapMarathonResponse] = Field(default_factory=list)
    peak_activity_date: date | None
    peak_activity_count: int
    genre_of_month: str | None
    genre_of_month_count: int = 0
    top_director_name: str | None = None
    top_director_count: int = 0
    top_director_kinopoisk_id: int | None = None
    top_country: str | None = None
    top_country_count: int = 0
    new_countries_count: int = 0
    genre_breakdown: list[MonthlyRecapDistributionItemResponse] = Field(default_factory=list)
    decade_breakdown: list[MonthlyRecapDecadeItemResponse] = Field(default_factory=list)
    director_breakdown: list[MonthlyRecapDirectorItemResponse] = Field(default_factory=list)
    franchise_breakdown: list[MonthlyRecapFranchiseItemResponse] = Field(default_factory=list)
    top_actor_kinopoisk_id: int | None = None
    top_actor_name: str | None = None
    top_actor_count: int = 0
    actor_breakdown: list[MonthlyRecapActorItemResponse] = Field(default_factory=list)
    collection_deltas: list[MonthlyRecapCollectionDeltaItemResponse] = Field(default_factory=list)
    achievements_unlocked: list[MonthlyRecapAchievementItemResponse] = Field(default_factory=list)
    streak_current: int = 0
    streak_best_in_period: int = 0
    vs_previous_total_rated: int | None = None
    vs_previous_average_rating: float | None = None
    dominant_mood_after: str | None = None
    dominant_company: str | None = None
    fun_facts: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


def build_monthly_recap_response(recap) -> MonthlyRecapResponse:
    from services.profile.build_monthly_recap import MonthlyRecap

    assert isinstance(recap, MonthlyRecap)
    return MonthlyRecapResponse(
        year=recap.year,
        month=recap.month,
        month_label=recap.month_label,
        total_rated=recap.total_rated,
        average_rating=recap.average_rating,
        top_films=[
            MonthlyRecapTopFilmResponse(
                card_id=item.card_id,
                film_id=item.film_id,
                title=item.title,
                poster_url=item.poster_url,
                rating=item.rating,
            )
            for item in recap.top_films
        ],
        new_stamps=[
            MonthlyRecapStampResponse(
                stamp_id=item.stamp_id,
                title=item.title,
                unlocked_at=item.unlocked_at,
            )
            for item in recap.new_stamps
        ],
        marathons_unlocked=[
            MonthlyRecapMarathonResponse(
                kind=item.kind,
                key=item.key,
                label=item.label,
                unlocked_at=item.unlocked_at,
            )
            for item in recap.marathons_unlocked
        ],
        peak_activity_date=recap.peak_activity_date,
        peak_activity_count=recap.peak_activity_count,
        genre_of_month=recap.genre_of_month,
        genre_of_month_count=recap.genre_of_month_count,
        top_director_name=recap.top_director_name,
        top_director_count=recap.top_director_count,
        top_director_kinopoisk_id=recap.top_director_kinopoisk_id,
        top_country=recap.top_country,
        top_country_count=recap.top_country_count,
        new_countries_count=recap.new_countries_count,
        genre_breakdown=[
            MonthlyRecapDistributionItemResponse(label=item.label, count=item.count)
            for item in recap.genre_breakdown
        ],
        decade_breakdown=[
            MonthlyRecapDecadeItemResponse(
                decade_start=item.decade_start,
                label=item.label,
                count=item.count,
            )
            for item in recap.decade_breakdown
        ],
        director_breakdown=[
            MonthlyRecapDirectorItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                label=item.label,
                count=item.count,
            )
            for item in recap.director_breakdown
        ],
        franchise_breakdown=[
            MonthlyRecapFranchiseItemResponse(
                franchise_key=item.franchise_key,
                label=item.label,
                count=item.count,
            )
            for item in recap.franchise_breakdown
        ],
        top_actor_kinopoisk_id=recap.top_actor_kinopoisk_id,
        top_actor_name=recap.top_actor_name,
        top_actor_count=recap.top_actor_count,
        actor_breakdown=[
            MonthlyRecapActorItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                label=item.label,
                count=item.count,
            )
            for item in recap.actor_breakdown
        ],
        collection_deltas=[
            MonthlyRecapCollectionDeltaItemResponse(
                collection_slug=item.collection_slug,
                title=item.title,
                films_rated_in_period=item.films_rated_in_period,
            )
            for item in recap.collection_deltas
        ],
        achievements_unlocked=[
            MonthlyRecapAchievementItemResponse(
                slug=item.slug,
                title=item.title,
                rarity_percent=item.rarity_percent,
            )
            for item in recap.achievements_unlocked
        ],
        streak_current=recap.streak_current,
        streak_best_in_period=recap.streak_best_in_period,
        vs_previous_total_rated=recap.vs_previous_total_rated,
        vs_previous_average_rating=recap.vs_previous_average_rating,
        dominant_mood_after=recap.dominant_mood_after,
        dominant_company=recap.dominant_company,
        fun_facts=list(recap.fun_facts),
    )


class FriendDigestLineResponse(BaseModel):
    author_user_id: UUID
    author_display: str
    profile_slug: str | None = None
    line_text: str

    model_config = ConfigDict(extra='forbid')


class FriendsDigestSectionResponse(BaseModel):
    telegram_lines: list[FriendDigestLineResponse] = Field(default_factory=list)
    in_app_items: list[FriendDigestLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')


class ControversyInsightResponse(BaseModel):
    film_title: str
    friend_display: str
    spread: float
    anchor_film_id: int | None = None

    model_config = ConfigDict(extra='forbid')


class PersonalDigestResponse(BaseModel):
    period: str
    period_key: str
    period_label: str
    year: int | None = None
    month: int | None = None
    month_label: str | None = None
    total_rated: int
    average_rating: float
    top_films: list[MonthlyRecapTopFilmResponse] = Field(default_factory=list)
    all_films: list[MonthlyRecapTopFilmResponse] = Field(default_factory=list)
    new_stamps: list[MonthlyRecapStampResponse] = Field(default_factory=list)
    marathons_unlocked: list[MonthlyRecapMarathonResponse] = Field(default_factory=list)
    peak_activity_date: date | None = None
    peak_activity_count: int = 0
    genre_of_month: str | None = None
    genre_of_month_count: int = 0
    top_director_name: str | None = None
    top_director_count: int = 0
    top_director_kinopoisk_id: int | None = None
    top_country: str | None = None
    top_country_count: int = 0
    new_countries_count: int = 0
    genre_breakdown: list[MonthlyRecapDistributionItemResponse] = Field(default_factory=list)
    decade_breakdown: list[MonthlyRecapDecadeItemResponse] = Field(default_factory=list)
    director_breakdown: list[MonthlyRecapDirectorItemResponse] = Field(default_factory=list)
    franchise_breakdown: list[MonthlyRecapFranchiseItemResponse] = Field(default_factory=list)
    top_actor_kinopoisk_id: int | None = None
    top_actor_name: str | None = None
    top_actor_count: int = 0
    actor_breakdown: list[MonthlyRecapActorItemResponse] = Field(default_factory=list)
    collection_deltas: list[MonthlyRecapCollectionDeltaItemResponse] = Field(default_factory=list)
    achievements_unlocked: list[MonthlyRecapAchievementItemResponse] = Field(default_factory=list)
    streak_current: int = 0
    streak_best_in_period: int = 0
    vs_previous_total_rated: int | None = None
    vs_previous_average_rating: float | None = None
    dominant_mood_after: str | None = None
    dominant_company: str | None = None
    fun_facts: list[str] = Field(default_factory=list)
    friends: FriendsDigestSectionResponse | None = None
    controversy: ControversyInsightResponse | None = None

    model_config = ConfigDict(extra='forbid')


def build_personal_digest_response(digest) -> PersonalDigestResponse:
    from services.personal_digest.build_personal_digest import PersonalDigestDTO

    assert isinstance(digest, PersonalDigestDTO)
    friends_response: FriendsDigestSectionResponse | None = None
    if digest.friends is not None:
        friends_response = FriendsDigestSectionResponse(
            telegram_lines=[
                FriendDigestLineResponse(
                    author_user_id=item.author_user_id,
                    author_display=item.author_display,
                    profile_slug=item.profile_slug,
                    line_text=item.line_text,
                )
                for item in digest.friends.telegram_lines
            ],
            in_app_items=[
                FriendDigestLineResponse(
                    author_user_id=item.author_user_id,
                    author_display=item.author_display,
                    profile_slug=item.profile_slug,
                    line_text=item.line_text,
                )
                for item in digest.friends.in_app_items
            ],
        )
    controversy_response: ControversyInsightResponse | None = None
    if digest.controversy is not None:
        controversy_response = ControversyInsightResponse(
            film_title=digest.controversy.film_title,
            friend_display=digest.controversy.friend_display,
            spread=digest.controversy.spread,
            anchor_film_id=digest.controversy.anchor_film_id,
        )
    return PersonalDigestResponse(
        period=digest.period,
        period_key=digest.period_key,
        period_label=digest.period_label,
        year=digest.year,
        month=digest.month,
        month_label=digest.period_label if digest.period == 'month' else None,
        total_rated=digest.total_rated,
        average_rating=digest.average_rating,
        top_films=[
            MonthlyRecapTopFilmResponse(
                card_id=item.card_id,
                film_id=item.film_id,
                title=item.title,
                poster_url=item.poster_url,
                rating=item.rating,
            )
            for item in digest.top_films
        ],
        all_films=[
            MonthlyRecapTopFilmResponse(
                card_id=item.card_id,
                film_id=item.film_id,
                title=item.title,
                poster_url=item.poster_url,
                rating=item.rating,
            )
            for item in digest.all_films
        ],
        new_stamps=[
            MonthlyRecapStampResponse(
                stamp_id=item.stamp_id,
                title=item.title,
                unlocked_at=item.unlocked_at,
            )
            for item in digest.new_stamps
        ],
        marathons_unlocked=[
            MonthlyRecapMarathonResponse(
                kind=item.kind,
                key=item.key,
                label=item.label,
                unlocked_at=item.unlocked_at,
            )
            for item in digest.marathons_unlocked
        ],
        peak_activity_date=digest.peak_activity_date,
        peak_activity_count=digest.peak_activity_count,
        genre_of_month=digest.genre_of_month,
        genre_of_month_count=digest.genre_of_month_count,
        top_director_name=digest.top_director_name,
        top_director_count=digest.top_director_count,
        top_director_kinopoisk_id=digest.top_director_kinopoisk_id,
        top_country=digest.top_country,
        top_country_count=digest.top_country_count,
        new_countries_count=digest.new_countries_count,
        genre_breakdown=[
            MonthlyRecapDistributionItemResponse(label=item.label, count=item.count)
            for item in digest.genre_breakdown
        ],
        decade_breakdown=[
            MonthlyRecapDecadeItemResponse(
                decade_start=item.decade_start,
                label=item.label,
                count=item.count,
            )
            for item in digest.decade_breakdown
        ],
        director_breakdown=[
            MonthlyRecapDirectorItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                label=item.label,
                count=item.count,
            )
            for item in digest.director_breakdown
        ],
        franchise_breakdown=[
            MonthlyRecapFranchiseItemResponse(
                franchise_key=item.franchise_key,
                label=item.label,
                count=item.count,
            )
            for item in digest.franchise_breakdown
        ],
        top_actor_kinopoisk_id=digest.top_actor_kinopoisk_id,
        top_actor_name=digest.top_actor_name,
        top_actor_count=digest.top_actor_count,
        actor_breakdown=[
            MonthlyRecapActorItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                label=item.label,
                count=item.count,
            )
            for item in digest.actor_breakdown
        ],
        collection_deltas=[
            MonthlyRecapCollectionDeltaItemResponse(
                collection_slug=item.collection_slug,
                title=item.title,
                films_rated_in_period=item.films_rated_in_period,
            )
            for item in digest.collection_deltas
        ],
        achievements_unlocked=[
            MonthlyRecapAchievementItemResponse(
                slug=item.slug,
                title=item.title,
                rarity_percent=item.rarity_percent,
            )
            for item in digest.achievements_unlocked
        ],
        streak_current=digest.streak_current,
        streak_best_in_period=digest.streak_best_in_period,
        vs_previous_total_rated=digest.vs_previous_total_rated,
        vs_previous_average_rating=digest.vs_previous_average_rating,
        dominant_mood_after=digest.dominant_mood_after,
        dominant_company=digest.dominant_company,
        fun_facts=list(digest.fun_facts),
        friends=friends_response,
        controversy=controversy_response,
    )
