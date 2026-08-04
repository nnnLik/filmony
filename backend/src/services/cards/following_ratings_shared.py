"""Shared DTOs and helpers for following-ratings services."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from models.user import User

FOLLOWING_RATINGS_TOP_LIMIT = 5


@dataclass(frozen=True, slots=True)
class FollowingRatingRow:
    user_id: UUID
    user_card_id: int
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    is_planned: bool
    rating: float | None


@dataclass(frozen=True, slots=True)
class ListFollowingRatingsResult:
    viewer_row: FollowingRatingRow | None
    items: list[FollowingRatingRow]


def pick_viewer_card_row(
    rows: list[tuple[User, float, int, bool]],
) -> tuple[User, float, int, bool] | None:
    for u, rating, user_card_id, is_planned in rows:
        if not is_planned and float(rating) >= 1:
            return u, rating, user_card_id, is_planned
    for u, rating, user_card_id, is_planned in rows:
        if is_planned:
            return u, rating, user_card_id, is_planned
    return None


def following_rating_row_from_parts(
    *,
    u: User,
    user_card_id: int,
    rating: float,
    is_planned: bool,
) -> FollowingRatingRow:
    planned_only = is_planned or rating < 1
    return FollowingRatingRow(
        user_id=u.id,
        user_card_id=user_card_id,
        profile_slug=u.profile_slug,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        photo_url=u.photo_url,
        display_name=u.display_name,
        is_planned=planned_only,
        rating=None if planned_only else rating,
    )
