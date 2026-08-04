from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from lib.genre_slug import genre_slug
from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters
from services.genres.resolve_genre_by_slug import ResolveGenreBySlugService


@dataclass(frozen=True, slots=True)
class GenreSummaryDTO:
    slug: str
    genre: str
    films_count: int
    avg_community_rating: float | None
    top_genres: list[str]


@dataclass
class GetGenreSummaryService:
    """Returns community summary for a genre slug."""

    _session: AsyncSession

    class GenreNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, slug: str) -> GenreSummaryDTO:
        genre_name = await ResolveGenreBySlugService.build(self._session).execute(slug)
        if genre_name is None:
            raise self.GenreNotFound

        stats_row = (
            await self._session.execute(
                select(
                    func.count(func.distinct(Film.id)),
                    func.avg(UserCard.rating),
                )
                .select_from(Film)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(
                    cast(Film.genres, JSONB).contains([genre_name]),
                    *_rated_card_filters(),
                ),
            )
        ).one()
        films_count = int(stats_row[0] or 0)
        if films_count == 0:
            raise self.GenreNotFound

        avg_raw = stats_row[1]
        avg_community_rating = round(float(avg_raw), 1) if avg_raw is not None else None

        return GenreSummaryDTO(
            slug=genre_slug(genre_name),
            genre=genre_name,
            films_count=films_count,
            avg_community_rating=avg_community_rating,
            top_genres=[genre_name],
        )
