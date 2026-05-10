from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.movie_card_tag import MovieCardTag


class MovieCardNotFoundError(Exception):
    pass


class MovieCardForbiddenError(Exception):
    pass


class MovieCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class UpdateMovieCardInput:
    rating: float | None = None
    company: CardCompany | None = None
    mood_before: CardMoodBefore | None = None
    mood_after: CardMoodAfter | None = None
    custom_tags: Sequence[str] | None = None
    watch_note: str | None = None
    is_favorite: bool | None = None


def _normalize_rating(value: float) -> float:
    if not isfinite(value):
        raise MovieCardValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise MovieCardValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise MovieCardValidationError('rating must be in [1, 10]')
    return snapped


def _normalize_watch_note(raw: str) -> str:
    s = raw.strip()
    if len(s) > 500:
        raise MovieCardValidationError('watch note max length is 500')
    return s


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


class UpdateMovieCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, card_id: int, viewer_user_id: UUID, payload: UpdateMovieCardInput
    ) -> MovieCard:
        card = (
            await self._session.execute(select(MovieCard).where(MovieCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise MovieCardNotFoundError
        if card.user_id != viewer_user_id:
            raise MovieCardForbiddenError
        if (
            payload.rating is None
            and payload.company is None
            and payload.mood_before is None
            and payload.mood_after is None
            and payload.custom_tags is None
            and payload.watch_note is None
            and payload.is_favorite is None
        ):
            raise MovieCardValidationError('at least one field must be provided')

        if payload.is_favorite is not None:
            if payload.is_favorite:
                card.is_favorite = True
                card.favorite_marked_at = dt.datetime.now(dt.UTC)
            else:
                card.is_favorite = False
                card.favorite_marked_at = None

        if payload.rating is not None:
            card.rating = _normalize_rating(payload.rating)
        if payload.company is not None:
            card.company = payload.company.value
        if payload.mood_before is not None:
            card.mood_before = payload.mood_before.value
        if payload.mood_after is not None:
            card.mood_after = payload.mood_after.value

        if payload.custom_tags is not None:
            tags = _normalize_tags(payload.custom_tags)
            await self._session.execute(
                delete(MovieCardTag).where(MovieCardTag.movie_card_id == card.id)
            )
            if tags:
                self._session.add_all(
                    [MovieCardTag(movie_card_id=card.id, tag=tag) for tag in tags]
                )

        if payload.watch_note is not None:
            card.watch_note = _normalize_watch_note(payload.watch_note)

        await self._session.commit()
        await self._session.refresh(card)
        return card
