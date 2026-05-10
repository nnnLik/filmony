from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag


@dataclass(frozen=True, slots=True)
class MovieCardTagStat:
    """Single custom tag aggregated across the user's movie cards."""

    tag: str
    use_count: int


class ListMyMovieCardTagStatsService:
    """Returns the viewer's custom tags with usage counts for autocomplete UIs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, *, limit: int) -> list[MovieCardTagStat]:
        cnt = func.count(MovieCardTag.movie_card_id)
        stmt = (
            select(MovieCardTag.tag, cnt)
            .join(MovieCard, MovieCard.id == MovieCardTag.movie_card_id)
            .where(MovieCard.user_id == user_id)
            .group_by(MovieCardTag.tag)
            .order_by(cnt.desc(), MovieCardTag.tag.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [MovieCardTagStat(tag=str(t), use_count=int(c)) for t, c in rows]
