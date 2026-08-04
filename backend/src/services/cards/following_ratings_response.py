"""Maps following-ratings service rows to API response schemas."""

from __future__ import annotations

from api.cards.schemas import FollowingRatingEntryResponse, FollowingRatingsListResponse
from services.cards.following_ratings_shared import (
    FollowingRatingRow,
    ListFollowingRatingsResult,
)


def following_rating_entry_response(row: FollowingRatingRow) -> FollowingRatingEntryResponse:
    return FollowingRatingEntryResponse(
        user_id=row.user_id,
        movie_card_id=row.user_card_id,
        profile_slug=row.profile_slug,
        username=row.username,
        first_name=row.first_name,
        last_name=row.last_name,
        photo_url=row.photo_url,
        display_name=row.display_name,
        rating=row.rating,
        is_planned=row.is_planned,
    )


def following_ratings_list_response(
    result: ListFollowingRatingsResult,
) -> FollowingRatingsListResponse:
    return FollowingRatingsListResponse(
        viewer_rating=(
            following_rating_entry_response(result.viewer_row)
            if result.viewer_row is not None
            else None
        ),
        items=[following_rating_entry_response(row) for row in result.items],
    )
