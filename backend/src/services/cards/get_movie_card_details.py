from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag


@dataclass(frozen=True, slots=True)
class MovieCardDetails:
    id: int
    user_id: UUID
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str]


class MovieCardNotFoundError(Exception):
    pass


class GetMovieCardDetailsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, card_id: int) -> MovieCardDetails:
        row = (
            await self._session.execute(
                select(MovieCard, Film)
                .join(Film, Film.id == MovieCard.film_id)
                .where(MovieCard.id == card_id)
            )
        ).one_or_none()
        if row is None:
            raise MovieCardNotFoundError()
        card, film = row

        tags = (
            (
                await self._session.execute(
                    select(MovieCardTag.tag)
                    .where(MovieCardTag.movie_card_id == card.id)
                    .order_by(MovieCardTag.tag)
                )
            )
            .scalars()
            .all()
        )
        return MovieCardDetails(
            id=card.id,
            user_id=card.user_id,
            film_id=film.id,
            film_kinopoisk_id=film.kinopoisk_id,
            film_genres=list(film.genres or []),
            film_title=film.title,
            film_year=film.year,
            film_poster_url=film.poster_url,
            rating=float(card.rating),
            company=card.company,
            mood_before=card.mood_before,
            mood_after=card.mood_after,
            custom_tags=list(tags),
        )
