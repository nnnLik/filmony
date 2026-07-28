"""Compute the most controversial title in a viewer's following circle."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.controversy.constants import MIN_SPREAD_FOR_TELEGRAM_DIGEST
from services.controversy.week_bounds import rating_window_start
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

MIN_RATER_COUNT = 3


@dataclass(frozen=True, slots=True)
class ControversyPolarCard:
    card_id: int
    author_display: str
    rating: float


@dataclass(frozen=True, slots=True)
class WeeklyControversyResult:
    anchor_film_id: int | None
    anchor_catalog_item_id: int | None
    title: str
    spread: float
    rater_count: int
    min_rating: float
    max_rating: float
    link_card_id: int | None = None
    film_year: int | None = None
    avg_rating: float | None = None
    polar_low: ControversyPolarCard | None = None
    polar_high: ControversyPolarCard | None = None
    viewer_rating: float | None = None


@dataclass(frozen=True, slots=True)
class WeeklyControversyBundle:
    primary: WeeklyControversyResult
    runner_up: WeeklyControversyResult | None = None


AnchorKind = Literal['film', 'catalog']


@dataclass(frozen=True, slots=True)
class _AnchorKey:
    kind: AnchorKind
    id: int


@dataclass(frozen=True, slots=True)
class _RatedCardRow:
    card_id: int
    user_id: UUID
    film_id: int | None
    catalog_item_id: int | None
    display_title: str | None
    rating: float
    completed_at: dt.datetime | None


@dataclass(frozen=True, slots=True)
class _AnchorCandidate:
    anchor: _AnchorKey
    stats: _SpreadStats


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
    ) -> WeeklyControversyBundle | None:
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

        candidates: list[_AnchorCandidate] = []
        for anchor in sorted(recent_anchors, key=_anchor_sort_key):
            stats = _controversy_for_anchor(
                cards=cards,
                anchor=anchor,
                window_start=window_start,
            )
            if stats is not None:
                candidates.append(_AnchorCandidate(anchor=anchor, stats=stats))

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item.stats.spread,
                -item.stats.rater_count,
                _anchor_sort_key(item.anchor),
            ),
        )

        user_ids = {card.user_id for card in cards}
        user_ids.add(viewer_user_id)
        display_by_user_id = await self._load_user_displays(user_ids)

        primary = await self._build_result_for_anchor(
            anchor=candidates[0].anchor,
            stats=candidates[0].stats,
            cards=cards,
            window_start=window_start,
            viewer_user_id=viewer_user_id,
            display_by_user_id=display_by_user_id,
        )

        runner_up: WeeklyControversyResult | None = None
        if len(candidates) > 1:
            second = candidates[1]
            if (
                second.stats.spread >= MIN_SPREAD_FOR_TELEGRAM_DIGEST
                and second.anchor != candidates[0].anchor
            ):
                candidate_result = await self._build_result_for_anchor(
                    anchor=second.anchor,
                    stats=second.stats,
                    cards=cards,
                    window_start=window_start,
                    viewer_user_id=viewer_user_id,
                    display_by_user_id=display_by_user_id,
                )
                if candidate_result.title != primary.title:
                    runner_up = candidate_result

        return WeeklyControversyBundle(primary=primary, runner_up=runner_up)

    async def enrich_persisted_result(
        self,
        *,
        result: WeeklyControversyResult,
        viewer_user_id: UUID,
        now: dt.datetime | None = None,
    ) -> WeeklyControversyResult:
        """Refresh live fields for a persisted week snapshot.

        Keeps stored spread/min/max/rater_count/title/anchors; recomputes polar cards,
        average, viewer rating, film year, and deeplink card from the current circle.
        """
        anchor = _anchor_key_from_result(result)
        if anchor is None:
            return result

        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=dt.UTC)
        else:
            now = now.astimezone(dt.UTC)

        viewer_rating = await self._load_viewer_rating(
            viewer_user_id=viewer_user_id,
            anchor=anchor,
        )
        film_year = result.film_year
        if anchor.kind == 'film' and film_year is None:
            film = await self._session.get(Film, anchor.id)
            if film is not None and film.year is not None:
                film_year = int(film.year)

        following_ids = await ListFollowingUserIdsForFollowerUserService.build(
            self._session
        ).execute(viewer_user_id)
        if not following_ids:
            return WeeklyControversyResult(
                anchor_film_id=result.anchor_film_id,
                anchor_catalog_item_id=result.anchor_catalog_item_id,
                title=result.title,
                spread=result.spread,
                rater_count=result.rater_count,
                min_rating=result.min_rating,
                max_rating=result.max_rating,
                link_card_id=result.link_card_id,
                film_year=film_year,
                avg_rating=result.avg_rating,
                polar_low=result.polar_low,
                polar_high=result.polar_high,
                viewer_rating=viewer_rating,
            )

        cards = await self._load_circle_rated_cards(following_ids)
        window_start = rating_window_start(now)
        anchor_cards = [card for card in cards if _card_matches_anchor(card, anchor)]
        recent_cards = [
            card for card in anchor_cards if _is_recent(card, window_start=window_start)
        ]
        effective_cards = recent_cards
        if _spread_from_ratings(_latest_ratings_by_user(recent_cards)) is None:
            effective_cards = anchor_cards

        ratings = list(_latest_ratings_by_user(effective_cards).values())
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        user_ids = {card.user_id for card in cards}
        user_ids.add(viewer_user_id)
        display_by_user_id = await self._load_user_displays(user_ids)
        polar_low, polar_high = _pick_polar_cards(
            cards=effective_cards,
            min_rating=result.min_rating,
            max_rating=result.max_rating,
            display_by_user_id=display_by_user_id,
        )
        link_card_id = result.link_card_id or _pick_link_card_id(
            cards=cards,
            anchor=anchor,
            max_rating=result.max_rating,
        )

        return WeeklyControversyResult(
            anchor_film_id=result.anchor_film_id,
            anchor_catalog_item_id=result.anchor_catalog_item_id,
            title=result.title,
            spread=result.spread,
            rater_count=result.rater_count,
            min_rating=result.min_rating,
            max_rating=result.max_rating,
            link_card_id=link_card_id,
            film_year=film_year,
            avg_rating=avg_rating,
            polar_low=polar_low,
            polar_high=polar_high,
            viewer_rating=viewer_rating,
        )

    async def _build_result_for_anchor(
        self,
        *,
        anchor: _AnchorKey,
        stats: _SpreadStats,
        cards: list[_RatedCardRow],
        window_start: dt.datetime,
        viewer_user_id: UUID,
        display_by_user_id: dict[UUID, str],
    ) -> WeeklyControversyResult:
        anchor_cards = [card for card in cards if _card_matches_anchor(card, anchor)]
        recent_cards = [
            card for card in anchor_cards if _is_recent(card, window_start=window_start)
        ]
        effective_cards = recent_cards
        if _spread_from_ratings(_latest_ratings_by_user(recent_cards)) is None:
            effective_cards = anchor_cards

        ratings = list(_latest_ratings_by_user(effective_cards).values())
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        polar_low, polar_high = _pick_polar_cards(
            cards=effective_cards,
            min_rating=stats.min_rating,
            max_rating=stats.max_rating,
            display_by_user_id=display_by_user_id,
        )

        title = await self._resolve_title(anchor=anchor, cards=cards)
        film_year: int | None = None
        if anchor.kind == 'film':
            film = await self._session.get(Film, anchor.id)
            if film is not None and film.year is not None:
                film_year = int(film.year)

        viewer_rating = await self._load_viewer_rating(
            viewer_user_id=viewer_user_id,
            anchor=anchor,
        )

        return WeeklyControversyResult(
            anchor_film_id=anchor.id if anchor.kind == 'film' else None,
            anchor_catalog_item_id=anchor.id if anchor.kind == 'catalog' else None,
            title=title,
            spread=stats.spread,
            rater_count=stats.rater_count,
            min_rating=stats.min_rating,
            max_rating=stats.max_rating,
            link_card_id=_pick_link_card_id(
                cards=cards,
                anchor=anchor,
                max_rating=stats.max_rating,
            ),
            film_year=film_year,
            avg_rating=avg_rating,
            polar_low=polar_low,
            polar_high=polar_high,
            viewer_rating=viewer_rating,
        )

    async def _load_viewer_rating(
        self,
        *,
        viewer_user_id: UUID,
        anchor: _AnchorKey,
    ) -> float | None:
        stmt = (
            select(UserCard.rating)
            .where(UserCard.user_id == viewer_user_id)
            .where(UserCard.is_planned.is_(False))
            .where(UserCard.rating >= 1)
        )
        if anchor.kind == 'film':
            stmt = stmt.where(UserCard.film_id == anchor.id)
        else:
            stmt = stmt.where(UserCard.catalog_item_id == anchor.id)
        stmt = stmt.order_by(UserCard.completed_at.desc().nullslast(), UserCard.id.desc()).limit(1)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return float(row) if row is not None else None

    async def _load_user_displays(self, user_ids: set[UUID]) -> dict[UUID, str]:
        if not user_ids:
            return {}
        rows = (
            (await self._session.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
        )
        return {user.id: _format_user_display(user) for user in rows}

    async def _load_circle_rated_cards(
        self,
        following_ids: tuple[UUID, ...],
    ) -> list[_RatedCardRow]:
        stmt = (
            select(
                UserCard.id,
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
                card_id=int(card_id),
                user_id=user_id,
                film_id=film_id,
                catalog_item_id=catalog_item_id,
                display_title=display_title,
                rating=float(rating),
                completed_at=completed_at,
            )
            for card_id, user_id, film_id, catalog_item_id, display_title, rating, completed_at in rows
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


def _format_user_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _anchor_key_from_result(result: WeeklyControversyResult) -> _AnchorKey | None:
    if result.anchor_film_id is not None:
        return _AnchorKey(kind='film', id=result.anchor_film_id)
    if result.anchor_catalog_item_id is not None:
        return _AnchorKey(kind='catalog', id=result.anchor_catalog_item_id)
    return None


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


def _latest_card_by_user(cards: list[_RatedCardRow]) -> dict[UUID, _RatedCardRow]:
    picked: dict[UUID, _RatedCardRow] = {}
    for card in cards:
        ts = _normalize_completed_at(card.completed_at) or dt.datetime.min.replace(tzinfo=dt.UTC)
        prev = picked.get(card.user_id)
        if prev is None:
            picked[card.user_id] = card
            continue
        prev_ts = _normalize_completed_at(prev.completed_at) or dt.datetime.min.replace(
            tzinfo=dt.UTC
        )
        if ts > prev_ts or (ts == prev_ts and card.card_id > prev.card_id):
            picked[card.user_id] = card
    return picked


def _latest_ratings_by_user(cards: list[_RatedCardRow]) -> dict[UUID, float]:
    return {user_id: card.rating for user_id, card in _latest_card_by_user(cards).items()}


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


def _pick_polar_card(
    *,
    latest_by_user: dict[UUID, _RatedCardRow],
    target_rating: float,
    display_by_user_id: dict[UUID, str],
) -> ControversyPolarCard | None:
    candidates = [card for card in latest_by_user.values() if card.rating == target_rating]
    if not candidates:
        return None
    best = max(
        candidates,
        key=lambda card: (
            _normalize_completed_at(card.completed_at) or dt.datetime.min.replace(tzinfo=dt.UTC),
            card.card_id,
        ),
    )
    return ControversyPolarCard(
        card_id=best.card_id,
        author_display=display_by_user_id.get(best.user_id, 'Пользователь'),
        rating=best.rating,
    )


def _pick_polar_cards(
    *,
    cards: list[_RatedCardRow],
    min_rating: float,
    max_rating: float,
    display_by_user_id: dict[UUID, str],
) -> tuple[ControversyPolarCard | None, ControversyPolarCard | None]:
    latest_by_user = _latest_card_by_user(cards)
    polar_low = _pick_polar_card(
        latest_by_user=latest_by_user,
        target_rating=min_rating,
        display_by_user_id=display_by_user_id,
    )
    polar_high = _pick_polar_card(
        latest_by_user=latest_by_user,
        target_rating=max_rating,
        display_by_user_id=display_by_user_id,
    )
    return polar_low, polar_high


def _pick_link_card_id(
    *,
    cards: list[_RatedCardRow],
    anchor: _AnchorKey,
    max_rating: float,
) -> int | None:
    candidates = [
        card for card in cards if _card_matches_anchor(card, anchor) and card.rating == max_rating
    ]
    if not candidates:
        return None
    best = max(
        candidates,
        key=lambda card: (
            _normalize_completed_at(card.completed_at) or dt.datetime.min.replace(tzinfo=dt.UTC),
            card.card_id,
        ),
    )
    return best.card_id
