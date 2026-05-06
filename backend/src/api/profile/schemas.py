from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.user import User
from services.profile.get_user_profile_counts import UserProfileCounts
from services.profile.list_user_movie_cards import MovieCardListItem, MovieCardPage
from services.subscriptions.list_user_subscriptions import (
    SubscriptionListItem,
)


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
    friends_count: int = 0

    model_config = ConfigDict(from_attributes=True)


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
    friends_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MovieCardItemResponse(BaseModel):
    id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str] = Field(default_factory=list)


class MovieCardPageResponse(BaseModel):
    items: list[MovieCardItemResponse] = Field(default_factory=list)
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
        friends_count=counts.friends,
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
        friends_count=counts.friends,
    )


def build_movie_card_page_response(page: MovieCardPage) -> MovieCardPageResponse:
    items = [
        MovieCardItemResponse(
            id=item.id,
            film_id=item.film_id,
            film_title=item.film_title,
            film_year=item.film_year,
            film_poster_url=item.film_poster_url,
            rating=item.rating,
            company=item.company,
            mood_before=item.mood_before,
            mood_after=item.mood_after,
            custom_tags=item.custom_tags,
        )
        for item in page.items
    ]
    return MovieCardPageResponse(items=items, next_cursor=page.next_cursor)


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
