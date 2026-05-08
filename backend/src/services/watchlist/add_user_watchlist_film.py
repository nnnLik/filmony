from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.user_watchlist_film import UserWatchlistFilm
from services.watchlist.list_user_watchlist_films import WatchlistFilmListItem


@dataclass
class AddUserWatchlistFilmService:
    """Adds a film to the current user's public «want to watch» list."""

    _session: AsyncSession

    class FilmNotFoundError(Exception):
        pass

    class MovieAlreadyRatedForFilmError(Exception):
        """User already has a rated movie card for this film."""

        pass

    class WatchlistFilmAlreadyListedError(Exception):
        pass

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, film_id: int) -> WatchlistFilmListItem:
        film = (
            await self._session.execute(select(Film).where(Film.id == film_id))
        ).scalar_one_or_none()
        if film is None:
            raise self.FilmNotFoundError

        has_card = (
            await self._session.execute(
                select(func.count(MovieCard.id)).where(
                    MovieCard.user_id == user_id,
                    MovieCard.film_id == film_id,
                )
            )
        ).scalar_one()
        if int(has_card or 0) > 0:
            raise self.MovieAlreadyRatedForFilmError

        row = UserWatchlistFilm(user_id=user_id, film_id=film_id)
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise self.WatchlistFilmAlreadyListedError from exc

        await self._session.commit()
        await self._session.refresh(row)
        return WatchlistFilmListItem(
            film_id=film.id,
            film_kinopoisk_id=film.kinopoisk_id,
            film_genres=list(film.genres or []),
            film_title=film.title,
            film_year=film.year,
            film_poster_url=film.poster_url,
            created_at=row.created_at,
        )
