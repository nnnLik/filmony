from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.movie_card_tag import MovieCardTag


class FilmNotFoundError(Exception):
    pass


class MovieCardAlreadyExistsError(Exception):
    pass


class MovieCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateMovieCardInput:
    film_id: int
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: Sequence[str]


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


class CreateMovieCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: CreateMovieCardInput) -> MovieCard:
        rating = _normalize_rating(payload.rating)
        custom_tags = _normalize_tags(payload.custom_tags)

        film = await self._session.execute(select(Film.id).where(Film.id == payload.film_id))
        if film.scalar_one_or_none() is None:
            raise FilmNotFoundError

        entity = MovieCard(
            user_id=user_id,
            film_id=payload.film_id,
            rating=rating,
            company=payload.company.value,
            mood_before=payload.mood_before.value,
            mood_after=payload.mood_after.value,
        )
        self._session.add(entity)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise MovieCardAlreadyExistsError from exc

        if custom_tags:
            self._session.add_all(
                [MovieCardTag(movie_card_id=entity.id, tag=tag) for tag in custom_tags]
            )
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
