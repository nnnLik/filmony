from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.card_tag import CardTag
from models.user_card import UserCard
from services.user_card_categories.resolve_user_card_category_id_for_owner import (
    ResolveUserCardCategoryIdForOwnerService,
)


class UserCardNotFoundError(Exception):
    pass


class UserCardForbiddenError(Exception):
    pass


class UserCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class UpdateUserCardInput:
    rating: float | None = None
    company: CardCompany | None = None
    mood_before: CardMoodBefore | None = None
    mood_after: CardMoodAfter | None = None
    custom_tags: Sequence[str] | None = None
    watch_note: str | None = None
    is_favorite: bool | None = None
    category_id: int | None = None


def _normalize_rating(value: float) -> float:
    if not isfinite(value):
        raise UserCardValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise UserCardValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise UserCardValidationError('rating must be in [1, 10]')
    return snapped


def _normalize_watch_note(raw: str) -> str:
    s = raw.strip()
    if len(s) > 500:
        raise UserCardValidationError('watch note max length is 500')
    return s


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip()
        if tag == '':
            continue
        if len(tag) > 40:
            raise UserCardValidationError('custom tag max length is 40')
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    if len(normalized) > 5:
        raise UserCardValidationError('max 5 custom tags allowed')
    return normalized


class UpdateUserCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, card_id: int, viewer_user_id: UUID, payload: UpdateUserCardInput
    ) -> UserCard:
        card = (
            await self._session.execute(select(UserCard).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise UserCardNotFoundError
        if card.user_id != viewer_user_id:
            raise UserCardForbiddenError
        if (
            payload.rating is None
            and payload.company is None
            and payload.mood_before is None
            and payload.mood_after is None
            and payload.custom_tags is None
            and payload.watch_note is None
            and payload.is_favorite is None
            and payload.category_id is None
        ):
            raise UserCardValidationError('at least one field must be provided')

        if card.is_planned and (
            payload.rating is not None
            or payload.mood_before is not None
            or payload.mood_after is not None
            or payload.custom_tags is not None
            or payload.is_favorite is not None
        ):
            raise UserCardValidationError(
                'cannot update rating, mood, tags, or favorite on planned cards'
            )

        if payload.category_id is not None:
            try:
                card.category_id = await ResolveUserCardCategoryIdForOwnerService.build(
                    self._session
                ).execute(viewer_user_id, payload.category_id)
            except ResolveUserCardCategoryIdForOwnerService.CategoryNotFoundForUserError as e:
                raise UserCardValidationError('category not found') from e

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
            await self._session.execute(delete(CardTag).where(CardTag.card_id == card.id))
            if tags:
                self._session.add_all([CardTag(card_id=card.id, tag=tag) for tag in tags])

        if payload.watch_note is not None:
            card.watch_note = _normalize_watch_note(payload.watch_note)

        await self._session.commit()
        await self._session.refresh(card)
        return card
