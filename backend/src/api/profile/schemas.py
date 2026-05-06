from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.user import User
from services.profile.get_user_profile_counts import UserProfileCounts
from services.profile.list_user_movie_cards import MovieCardPage


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)
    profile_slug: str | None = Field(default=None, min_length=3, max_length=32)

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


class MovieCardPageResponse(BaseModel):
    """Paginated movie cards; v1 returns an empty ``items`` list until feature 005."""

    items: list[dict[str, object]] = Field(default_factory=list)
    next_cursor: str | None = None


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
    return MovieCardPageResponse(items=[], next_cursor=page.next_cursor)
