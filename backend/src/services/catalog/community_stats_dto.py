from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommunityStatsDTO:
    avg_rating: float | None
    ratings_count: int


def is_contrarian(
    *,
    user_rating: float,
    avg_rating: float | None,
    ratings_count: int,
) -> bool:
    """True when community has enough ratings and user diverges by >= 4 points."""
    if ratings_count < 3 or avg_rating is None:
        return False
    return abs(user_rating - avg_rating) >= 4.0
