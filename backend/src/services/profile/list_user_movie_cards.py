from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MovieCardPage:
    items: list[object]
    next_cursor: str | None


class ListUserMovieCardsService:
    """Paginated movie cards for a profile; v1 returns an empty page (contract for feature 005)."""

    async def execute(
        self,
        user_id: UUID,  # noqa: ARG002
        cursor: str | None,  # noqa: ARG002
        limit: int,  # noqa: ARG002
    ) -> MovieCardPage:
        return MovieCardPage(items=[], next_cursor=None)
