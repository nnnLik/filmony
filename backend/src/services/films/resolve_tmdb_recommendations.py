from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from providers.tmdb.tmdb_snapshot_recommendations import extract_tmdb_recommendation_entries


@dataclass(frozen=True, slots=True)
class ResolvedRecommendationDTO:
    title: str
    film_id: int | None
    in_catalog: bool


@dataclass
class ResolveTmdbRecommendationsService:
    """Resolves TMDB snapshot recommendations to catalog Film rows when possible."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, film: Film) -> list[ResolvedRecommendationDTO]:
        entries = extract_tmdb_recommendation_entries(film.tmdb_detail_snapshot_json)
        if not entries:
            return []

        tmdb_ids = [entry.tmdb_id for entry in entries if entry.tmdb_id is not None]
        films_by_tmdb_id: dict[int, int] = {}
        if tmdb_ids:
            rows = (
                await self._session.execute(
                    select(Film.id, Film.tmdb_id).where(Film.tmdb_id.in_(tmdb_ids)),
                )
            ).all()
            films_by_tmdb_id = {int(tmdb_id): int(film_id) for film_id, tmdb_id in rows}

        unresolved_titles: list[str] = []
        for entry in entries:
            if entry.tmdb_id is not None and entry.tmdb_id in films_by_tmdb_id:
                continue
            unresolved_titles.append(entry.title)

        films_by_title: dict[str, int] = {}
        if unresolved_titles:
            lower_titles = [title.lower() for title in unresolved_titles]
            rows = (
                await self._session.execute(
                    select(Film.id, Film.title).where(func.lower(Film.title).in_(lower_titles)),
                )
            ).all()
            for film_id, title in rows:
                key = str(title).strip().lower()
                if key and key not in films_by_title:
                    films_by_title[key] = int(film_id)

        resolved: list[ResolvedRecommendationDTO] = []
        for entry in entries:
            film_id: int | None = None
            if entry.tmdb_id is not None:
                film_id = films_by_tmdb_id.get(entry.tmdb_id)
            if film_id is None:
                film_id = films_by_title.get(entry.title.lower())
            resolved.append(
                ResolvedRecommendationDTO(
                    title=entry.title,
                    film_id=film_id,
                    in_catalog=film_id is not None,
                ),
            )
        return resolved


__all__ = ('ResolveTmdbRecommendationsService', 'ResolvedRecommendationDTO')
