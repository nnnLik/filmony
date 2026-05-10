from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.movie_card_tag import MovieCardTag
from models.user_watchlist_film import UserWatchlistFilm


class FilmNotFoundError(Exception):
    pass


class MovieCardAlreadyExistsError(Exception):
    pass


class MovieCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateMovieCardInput:
    film_id: int
    kinopoisk_id: int
    genres: Sequence[str]
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: Sequence[str]
    watch_note: str = ''


def _normalize_rating(value: float) -> float:
    if not isfinite(value):
        raise MovieCardValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise MovieCardValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise MovieCardValidationError('rating must be in [1, 10]')
    return snapped


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip()
        if tag == '':
            continue
        if len(tag) > 40:
            raise MovieCardValidationError('custom tag max length is 40')
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    if len(normalized) > 5:
        raise MovieCardValidationError('max 5 custom tags allowed')
    return normalized


def _normalize_watch_note(raw: str) -> str:
    s = (raw or '').strip()
    if len(s) > 500:
        raise MovieCardValidationError('watch note max length is 500')
    return s


def _normalize_genres(genres: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in genres:
        genre = raw.strip()
        if genre == '':
            continue
        if len(genre) > 80:
            raise MovieCardValidationError('genre max length is 80')
        key = genre.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(genre)
    if len(normalized) > 20:
        raise MovieCardValidationError('max 20 genres allowed')
    return normalized


class CreateMovieCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: CreateMovieCardInput) -> MovieCard:
        rating = _normalize_rating(payload.rating)
        custom_tags = _normalize_tags(payload.custom_tags)
        watch_note = _normalize_watch_note(payload.watch_note)
        genres = _normalize_genres(payload.genres)

        film_result = await self._session.execute(select(Film).where(Film.id == payload.film_id))
        film = film_result.scalar_one_or_none()
        if film is None:
            raise FilmNotFoundError
        if film.kinopoisk_id != payload.kinopoisk_id:
            raise MovieCardValidationError('kinopoisk_id does not match film_id')
        if genres != (film.genres or []):
            film.genres = genres

        entity = MovieCard(
            user_id=user_id,
            film_id=payload.film_id,
            rating=rating,
            company=payload.company.value,
            mood_before=payload.mood_before.value,
            mood_after=payload.mood_after.value,
            watch_note=watch_note,
        )
        self._session.add(entity)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise MovieCardAlreadyExistsError from exc

        await self._session.execute(
            delete(UserWatchlistFilm).where(
                UserWatchlistFilm.user_id == user_id,
                UserWatchlistFilm.film_id == payload.film_id,
            )
        )

        if custom_tags:
            self._session.add_all(
                [MovieCardTag(movie_card_id=entity.id, tag=tag) for tag in custom_tags]
            )
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
