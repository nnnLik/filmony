"""Compute the most controversial title in a viewer's following circle."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.controversy.week_bounds import rating_window_start
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)

MIN_RATER_COUNT = 3


@dataclass(frozen=True, slots=True)
class WeeklyControversyResult:
    anchor_film_id: int | None
    anchor_catalog_item_id: int | None
    title: str
    spread: float
    rater_count: int
    min_rating: float
    max_rating: float


AnchorKind = Literal['film', 'catalog']


@dataclass(frozen=True, slots=True)
class _AnchorKey:
    kind: AnchorKind
    id: int


@dataclass(frozen=True, slots=True)
class _RatedCardRow:
    user_id: UUID
    film_id: int | None
    catalog_item_id: int | None
    display_title: str | None
    rating: float
    completed_at: dt.datetime | None


@dataclass
class ComputeWeeklyControversyService:
    """Picks the highest rating spread among circle titles with enough distinct raters.

    Prefers ratings completed in the rolling last-seven-days window. When an anchor had
    recent circle activity but fewer than three recent raters, falls back to all-time
    ratings from the circle for that anchor.
    """

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        viewer_user_id: UUID,
        now: dt.datetime | None = None,
    ) -> WeeklyControversyResult | None:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=dt.UTC)
        else:
            now = now.astimezone(dt.UTC)

        following_ids = await ListFollowingUserIdsForFollowerUserService.build(
            self._session
        ).execute(viewer_user_id)
        if not following_ids:
            return None

        window_start = rating_window_start(now)
        cards = await self._load_circle_rated_cards(following_ids)
        if not cards:
            return None

        recent_anchors = _anchors_with_recent_activity(cards, window_start=window_start)
        if not recent_anchors:
            return None

        best: WeeklyControversyResult | None = None
        for anchor in sorted(recent_anchors, key=_anchor_sort_key):
            stats = _controversy_for_anchor(
                cards=cards,
                anchor=anchor,
                window_start=window_start,
            )
            if stats is None:
                continue
            if best is None or _is_better_candidate(stats, best):
                title = await self._resolve_title(anchor=anchor, cards=cards)
                best = WeeklyControversyResult(
                    anchor_film_id=anchor.id if anchor.kind == 'film' else None,
                    anchor_catalog_item_id=anchor.id if anchor.kind == 'catalog' else None,
                    title=title,
                    spread=stats.spread,
                    rater_count=stats.rater_count,
                    min_rating=stats.min_rating,
                    max_rating=stats.max_rating,
                )
        return best

    async def _load_circle_rated_cards(
        self,
        following_ids: tuple[UUID, ...],
    ) -> list[_RatedCardRow]:
        stmt = (
            select(
                UserCard.user_id,
                UserCard.film_id,
                UserCard.catalog_item_id,
                UserCard.display_title,
                UserCard.rating,
                UserCard.completed_at,
            )
            .where(UserCard.user_id.in_(following_ids))
            .where(UserCard.is_planned.is_(False))
            .where(UserCard.rating >= 1)
            .where(or_(UserCard.film_id.isnot(None), UserCard.catalog_item_id.isnot(None)))
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            _RatedCardRow(
                user_id=user_id,
                film_id=film_id,
                catalog_item_id=catalog_item_id,
                display_title=display_title,
                rating=float(rating),
                completed_at=completed_at,
            )
            for user_id, film_id, catalog_item_id, display_title, rating, completed_at in rows
        ]

    async def _resolve_title(
        self,
        *,
        anchor: _AnchorKey,
        cards: list[_RatedCardRow],
    ) -> str:
        if anchor.kind == 'film':
            film = await self._session.get(Film, anchor.id)
            if film is not None and film.title:
                return film.title
        for card in cards:
            key = _anchor_key_from_parts(card.film_id, card.catalog_item_id)
            if key == anchor and card.display_title:
                return card.display_title
        return 'Без названия'


@dataclass(frozen=True, slots=True)
class _SpreadStats:
    spread: float
    rater_count: int
    min_rating: float
    max_rating: float


def _anchor_key_from_parts(film_id: int | None, catalog_item_id: int | None) -> _AnchorKey | None:
    if film_id is not None:
        return _AnchorKey(kind='film', id=film_id)
    if catalog_item_id is not None:
        return _AnchorKey(kind='catalog', id=catalog_item_id)
    return None


def _anchor_sort_key(anchor: _AnchorKey) -> tuple[str, int]:
    return (anchor.kind, anchor.id)


def _card_matches_anchor(card: _RatedCardRow, anchor: _AnchorKey) -> bool:
    key = _anchor_key_from_parts(card.film_id, card.catalog_item_id)
    return key == anchor


def _normalize_completed_at(value: dt.datetime | None) -> dt.datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value.astimezone(dt.UTC)


def _is_recent(card: _RatedCardRow, *, window_start: dt.datetime) -> bool:
    completed_at = _normalize_completed_at(card.completed_at)
    return completed_at is not None and completed_at >= window_start


def _anchors_with_recent_activity(
    cards: list[_RatedCardRow],
    *,
    window_start: dt.datetime,
) -> set[_AnchorKey]:
    anchors: set[_AnchorKey] = set()
    for card in cards:
        if not _is_recent(card, window_start=window_start):
            continue
        key = _anchor_key_from_parts(card.film_id, card.catalog_item_id)
        if key is not None:
            anchors.add(key)
    return anchors


def _latest_ratings_by_user(cards: list[_RatedCardRow]) -> dict[UUID, float]:
    picked: dict[UUID, tuple[dt.datetime, float]] = {}
    for card in cards:
        ts = _normalize_completed_at(card.completed_at) or dt.datetime.min.replace(tzinfo=dt.UTC)
        prev = picked.get(card.user_id)
        if prev is None or ts > prev[0]:
            picked[card.user_id] = (ts, card.rating)
    return {user_id: rating for user_id, (_, rating) in picked.items()}


def _spread_from_ratings(ratings: dict[UUID, float]) -> _SpreadStats | None:
    if len(ratings) < MIN_RATER_COUNT:
        return None
    values = list(ratings.values())
    min_rating = min(values)
    max_rating = max(values)
    return _SpreadStats(
        spread=max_rating - min_rating,
        rater_count=len(ratings),
        min_rating=min_rating,
        max_rating=max_rating,
    )


def _controversy_for_anchor(
    *,
    cards: list[_RatedCardRow],
    anchor: _AnchorKey,
    window_start: dt.datetime,
) -> _SpreadStats | None:
    anchor_cards = [card for card in cards if _card_matches_anchor(card, anchor)]
    recent_cards = [card for card in anchor_cards if _is_recent(card, window_start=window_start)]
    recent_stats = _spread_from_ratings(_latest_ratings_by_user(recent_cards))
    if recent_stats is not None:
        return recent_stats
    return _spread_from_ratings(_latest_ratings_by_user(anchor_cards))


def _is_better_candidate(
    candidate: WeeklyControversyResult | _SpreadStats,
    current: WeeklyControversyResult,
) -> bool:
    spread = candidate.spread
    rater_count = candidate.rater_count
    if spread > current.spread:
        return True
    if spread < current.spread:
        return False
    if rater_count > current.rater_count:
        return True
    if rater_count < current.rater_count:
        return False
    return False
