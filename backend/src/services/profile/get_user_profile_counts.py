from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserProfileCounts:
    movie_cards: int
    friends: int


class GetUserProfileCountsService:
    """Aggregate counts for profile headers; v1 returns zeros until cards/friends ship."""

    async def execute(self, user_id: UUID) -> UserProfileCounts:  # noqa: ARG002
        return UserProfileCounts(movie_cards=0, friends=0)
