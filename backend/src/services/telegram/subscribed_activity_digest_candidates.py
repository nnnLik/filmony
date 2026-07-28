"""Collect and select subscribed-activity digest insight candidates."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import random
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.feed_post import FeedPost
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)

DIGEST_INTERVAL = dt.timedelta(hours=48)
MIN_CANDIDATE_SCORE = 40.0
MAX_POOL_SIZE = 30
DIGEST_ITEM_COUNT = 3

_INLINE_TOKEN_RE = re.compile(r'⟦[^⟧]+⟧')


def _ensure_naive_utc(ts: dt.datetime) -> dt.datetime:
    if ts.tzinfo is None:
        return ts
    return ts.astimezone(dt.UTC).replace(tzinfo=None)


class DigestCandidateKind(StrEnum):
    new_user_card = 'new_user_card'
    new_feed_post = 'new_feed_post'
    high_rating_card = 'high_rating_card'
    author_activity_summary = 'author_activity_summary'


@dataclass(frozen=True, slots=True)
class DigestCandidate:
    kind: DigestCandidateKind
    author_user_id: UUID
    author_display: str
    score: float
    occurred_at: dt.datetime
    line_html: str
    entity_key: str
    card_id: int | None = None
    feed_post_id: int | None = None
    film_title: str | None = None
    film_year: int | None = None
    film_genres: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    rating: float | None = None
    is_favorite: bool = False
    mood_after: str | None = None
    post_snippet: str | None = None
    activity_card_count: int | None = None
    activity_post_count: int | None = None


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _card_title(*, film: Film | None, card: UserCard) -> str:
    if film is not None and (film.title or '').strip():
        return (film.title or '').strip()
    manual = (card.display_title or '').strip()
    return manual or 'Карточка'


def _snippet_from_body(body: str, max_len: int = 120) -> str:
    raw = _INLINE_TOKEN_RE.sub(' ', body)
    raw = ' '.join(raw.split()).strip()
    if len(raw) <= max_len:
        return raw
    return raw[: max_len - 1] + '…'


def _freshness_bonus(occurred_at: dt.datetime, window_end: dt.datetime) -> float:
    occurred_at = _ensure_naive_utc(occurred_at)
    window_end = _ensure_naive_utc(window_end)
    age_hours = max(0.0, (window_end - occurred_at).total_seconds() / 3600.0)
    return max(0.0, 24.0 - age_hours)


def _deterministic_rng(*, recipient_user_id: UUID, window_start: dt.datetime) -> random.Random:
    seed_material = f'{recipient_user_id}:{window_start.isoformat()}'.encode()
    seed_int = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], 'big')
    return random.Random(seed_int)


def _payload_hash(candidates: list[DigestCandidate]) -> str:
    parts = sorted(c.entity_key for c in candidates)
    joined = '|'.join(parts)
    return hashlib.sha256(joined.encode()).hexdigest()


@dataclass
class CollectSubscribedActivityDigestCandidatesService:
    """Loads scored digest candidates for followed users within a time window."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[DigestCandidate]:
        if not following_user_ids:
            return []

        window_start = _ensure_naive_utc(window_start)
        window_end = _ensure_naive_utc(window_end)

        card_rows = await self._load_card_rows(following_user_ids, window_start, window_end)
        post_rows = await self._load_post_rows(following_user_ids, window_start, window_end)

        candidates: list[DigestCandidate] = []
        author_card_counts: dict[UUID, int] = {}
        author_post_counts: dict[UUID, int] = {}

        card_ids = [int(card.id) for card, _, _ in card_rows]
        tags_by_card = await self._load_tags_by_card_id(card_ids)
        self._append_card_candidates(
            candidates,
            author_card_counts,
            card_rows,
            tags_by_card,
            window_end,
        )
        self._append_post_candidates(
            candidates,
            author_post_counts,
            post_rows,
            window_end,
        )
        await self._append_author_summary_candidates(
            candidates,
            author_card_counts,
            author_post_counts,
            window_end,
        )

        filtered = [c for c in candidates if c.score >= MIN_CANDIDATE_SCORE]
        filtered.sort(key=lambda c: (-c.score, c.entity_key))
        return filtered[:MAX_POOL_SIZE]

    async def _load_card_rows(
        self,
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ):
        return (
            await self._session.execute(
                select(UserCard, User, Film)
                .join(User, User.id == UserCard.user_id)
                .outerjoin(Film, Film.id == UserCard.film_id)
                .where(UserCard.user_id.in_(following_user_ids))
                .where(UserCard.created_at >= window_start)
                .where(UserCard.created_at < window_end)
                .where(UserCard.is_planned.is_(False))
                .where(UserCard.rating >= 1.0)
                .order_by(UserCard.created_at.desc(), UserCard.id.desc())
            )
        ).all()

    async def _load_post_rows(
        self,
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ):
        return (
            await self._session.execute(
                select(FeedPost, User)
                .join(User, User.id == FeedPost.user_id)
                .where(FeedPost.user_id.in_(following_user_ids))
                .where(FeedPost.created_at >= window_start)
                .where(FeedPost.created_at < window_end)
                .order_by(FeedPost.created_at.desc(), FeedPost.id.desc())
            )
        ).all()

    def _append_card_candidates(
        self,
        candidates: list[DigestCandidate],
        author_card_counts: dict[UUID, int],
        card_rows,
        tags_by_card: dict[int, tuple[str, ...]],
        window_end: dt.datetime,
    ) -> None:
        for card, author, film in card_rows:
            author_card_counts[author.id] = author_card_counts.get(author.id, 0) + 1
            title_raw = _card_title(film=film, card=card)
            title = html.escape(title_raw)
            rating = float(card.rating)
            display = html.escape(_format_actor_display(author))
            occurred_at = card.created_at
            freshness = _freshness_bonus(occurred_at, window_end)
            base_score = 100.0 + freshness
            if rating >= 9.0:
                base_score += 25.0
            if card.is_favorite:
                base_score += 10.0

            genres = tuple(g for g in (film.genres if film is not None else []) if g)
            tags = tags_by_card.get(int(card.id), ())
            film_year = int(film.year) if film is not None and film.year is not None else None
            mood_after = card.mood_after if card.mood_after else None

            fav_suffix = ' и добавил(а) её в любимое' if card.is_favorite else ''
            line = (
                f'<b>{display}</b> опубликовал(а) карточку «{title}» '
                f'с оценкой {rating:.0f}{fav_suffix}'
            )
            candidates.append(
                DigestCandidate(
                    kind=DigestCandidateKind.new_user_card,
                    author_user_id=author.id,
                    author_display=display,
                    score=base_score,
                    occurred_at=occurred_at,
                    line_html=line,
                    entity_key=f'card:{card.id}',
                    card_id=int(card.id),
                    film_title=title_raw,
                    film_year=film_year,
                    film_genres=genres,
                    tags=tags,
                    rating=rating,
                    is_favorite=bool(card.is_favorite),
                    mood_after=mood_after,
                )
            )

            if rating >= 9.0:
                candidates.append(
                    DigestCandidate(
                        kind=DigestCandidateKind.high_rating_card,
                        author_user_id=author.id,
                        author_display=display,
                        score=95.0 + freshness + (rating - 9.0) * 5.0,
                        occurred_at=occurred_at,
                        line_html=(
                            f'<b>{display}</b> поставил(а) «{title}» '
                            f'очень высокую оценку — {rating:.0f}/10'
                        ),
                        entity_key=f'high:{card.id}',
                        card_id=int(card.id),
                        film_title=title_raw,
                        film_year=film_year,
                        film_genres=genres,
                        tags=tags,
                        rating=rating,
                        is_favorite=bool(card.is_favorite),
                        mood_after=mood_after,
                    )
                )

    def _append_post_candidates(
        self,
        candidates: list[DigestCandidate],
        author_post_counts: dict[UUID, int],
        post_rows,
        window_end: dt.datetime,
    ) -> None:
        for post, author in post_rows:
            author_post_counts[author.id] = author_post_counts.get(author.id, 0) + 1
            snippet = _snippet_from_body(post.body or '')
            if not snippet:
                continue
            display = html.escape(_format_actor_display(author))
            freshness = _freshness_bonus(post.created_at, window_end)
            score = 90.0 + freshness + min(len(snippet), 80) * 0.1
            safe_snippet = html.escape(snippet)
            candidates.append(
                DigestCandidate(
                    kind=DigestCandidateKind.new_feed_post,
                    author_user_id=author.id,
                    author_display=display,
                    score=score,
                    occurred_at=post.created_at,
                    line_html=f'<b>{display}</b> опубликовал(а) пост: «{safe_snippet}»',
                    entity_key=f'post:{post.id}',
                    feed_post_id=int(post.id),
                    post_snippet=snippet,
                )
            )

    async def _append_author_summary_candidates(
        self,
        candidates: list[DigestCandidate],
        author_card_counts: dict[UUID, int],
        author_post_counts: dict[UUID, int],
        window_end: dt.datetime,
    ) -> None:
        author_ids = set(author_card_counts) | set(author_post_counts)
        for author_id in author_ids:
            card_count = author_card_counts.get(author_id, 0)
            post_count = author_post_counts.get(author_id, 0)
            total = card_count + post_count
            if total < 2:
                continue
            author = await self._session.get(User, author_id)
            if author is None:
                continue
            display = html.escape(_format_actor_display(author))
            candidates.append(
                DigestCandidate(
                    kind=DigestCandidateKind.author_activity_summary,
                    author_user_id=author_id,
                    author_display=display,
                    score=55.0 + min(total, 10) * 3.0,
                    occurred_at=window_end,
                    line_html=(
                        f'<b>{display}</b> был(а) особенно активен(а): '
                        f'{total} новых событий за 48 часов'
                    ),
                    entity_key=f'summary:{author_id}',
                    activity_card_count=card_count or None,
                    activity_post_count=post_count or None,
                )
            )

    async def _load_tags_by_card_id(self, card_ids: list[int]) -> dict[int, tuple[str, ...]]:
        if not card_ids:
            return {}
        rows = (
            await self._session.execute(
                select(CardTag.card_id, CardTag.tag)
                .where(CardTag.card_id.in_(card_ids))
                .order_by(CardTag.card_id, CardTag.tag)
            )
        ).all()
        out: dict[int, list[str]] = {}
        for card_id, tag in rows:
            out.setdefault(int(card_id), []).append(tag.strip())
        return {cid: tuple(tags) for cid, tags in out.items()}


@dataclass
class SelectSubscribedActivityDigestItemsService:
    """Picks up to three digest items from a scored pool with diversity constraints."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute(
        self,
        *,
        pool: list[DigestCandidate],
        recipient_user_id: UUID,
        window_start: dt.datetime,
        limit: int = DIGEST_ITEM_COUNT,
    ) -> list[DigestCandidate]:
        if not pool:
            return []

        rng = _deterministic_rng(
            recipient_user_id=recipient_user_id,
            window_start=window_start,
        )

        by_author_kind: dict[tuple[UUID, DigestCandidateKind], DigestCandidate] = {}
        for candidate in pool:
            key = (candidate.author_user_id, candidate.kind)
            prev = by_author_kind.get(key)
            if prev is None or candidate.score > prev.score:
                by_author_kind[key] = candidate

        deduped = list(by_author_kind.values())
        deduped.sort(key=lambda c: (-c.score, c.entity_key))

        selected: list[DigestCandidate] = []
        author_counts: dict[UUID, int] = {}
        kind_counts: dict[DigestCandidateKind, int] = {}

        def _can_add(candidate: DigestCandidate) -> bool:
            if author_counts.get(candidate.author_user_id, 0) >= 1:
                return False
            return kind_counts.get(candidate.kind, 0) < 2

        remaining = deduped[:]
        while remaining and len(selected) < limit:
            eligible = [c for c in remaining if _can_add(c)]
            if not eligible:
                break
            weights = [max(c.score, 1.0) for c in eligible]
            pick = rng.choices(eligible, weights=weights, k=1)[0]
            selected.append(pick)
            author_counts[pick.author_user_id] = author_counts.get(pick.author_user_id, 0) + 1
            kind_counts[pick.kind] = kind_counts.get(pick.kind, 0) + 1
            remaining = [c for c in remaining if c.entity_key != pick.entity_key]

        if len(selected) < limit:
            for candidate in deduped:
                if candidate in selected:
                    continue
                if candidate.author_user_id in {s.author_user_id for s in selected}:
                    continue
                selected.append(candidate)
                if len(selected) >= limit:
                    break

        if len(selected) < limit:
            for candidate in deduped:
                if candidate in selected:
                    continue
                selected.append(candidate)
                if len(selected) >= limit:
                    break

        return selected[:limit]


def digest_payload_hash(candidates: list[DigestCandidate]) -> str:
    if not candidates:
        return hashlib.sha256(b'empty').hexdigest()
    return _payload_hash(candidates)
