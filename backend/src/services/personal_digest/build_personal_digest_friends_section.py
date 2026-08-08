"""Weekly friends block for personal digest."""

from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.achievement import Achievement
from models.collection import Collection
from models.collection_film import CollectionFilm
from models.film import Film
from models.user import User
from models.user_achievement import UserAchievement
from models.user_card import UserCard
from services.profile.build_monthly_recap import _completion_timestamp
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)
from services.telegram.subscribed_activity_digest_candidates import (
    CollectSubscribedActivityDigestCandidatesService,
    DigestCandidate,
    DigestCandidateKind,
)


def _format_friend_display(user: User) -> str:
    if user.username and user.username.strip():
        return f'@{user.username.strip()}'
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    return 'Друг'


@dataclass(frozen=True, slots=True)
class FriendDigestLine:
    author_user_id: UUID
    author_display: str
    profile_slug: str | None
    line_text: str


@dataclass(frozen=True, slots=True)
class FriendsDigestSection:
    telegram_lines: tuple[FriendDigestLine, ...]
    in_app_items: tuple[FriendDigestLine, ...]


@dataclass(frozen=True, slots=True)
class _FriendCandidate:
    author_user_id: UUID
    score: float
    line_text: str
    entity_key: str


@dataclass
class BuildPersonalDigestFriendsSectionService:
    """Builds the weekly friends activity block from following users."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        recipient_user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> FriendsDigestSection | None:
        following_ids = await ListFollowingUserIdsForFollowerUserService.build(
            self._session
        ).execute(recipient_user_id)
        if not following_ids:
            return None

        following_tuple = tuple(following_ids)
        pool = await CollectSubscribedActivityDigestCandidatesService.build(self._session).execute(
            following_user_ids=following_tuple,
            window_start=window_start,
            window_end=window_end,
        )
        candidates = await self._extend_candidates(
            pool=pool,
            following_user_ids=following_tuple,
            window_start=window_start,
            window_end=window_end,
        )
        if not candidates:
            return None

        users_by_id = await self._load_users({c.author_user_id for c in candidates})
        scored: list[_FriendCandidate] = []
        for candidate in candidates:
            user = users_by_id.get(candidate.author_user_id)
            if user is None:
                continue
            line_text = self._line_text_for_candidate(candidate)
            if not line_text:
                continue
            scored.append(
                _FriendCandidate(
                    author_user_id=candidate.author_user_id,
                    score=candidate.score,
                    line_text=line_text,
                    entity_key=candidate.entity_key,
                )
            )
        if not scored:
            return None

        telegram_keys = self._select_diverse(scored, limit=3)
        in_app_keys = self._select_diverse(scored, limit=8)

        def _to_line(item: _FriendCandidate) -> FriendDigestLine:
            user = users_by_id[item.author_user_id]
            return FriendDigestLine(
                author_user_id=item.author_user_id,
                author_display=_format_friend_display(user),
                profile_slug=user.profile_slug,
                line_text=item.line_text,
            )

        telegram_lines = tuple(
            _to_line(item) for item in scored if item.entity_key in telegram_keys
        )
        in_app_items = tuple(_to_line(item) for item in scored if item.entity_key in in_app_keys)
        return FriendsDigestSection(
            telegram_lines=telegram_lines,
            in_app_items=in_app_items,
        )

    async def _load_users(self, user_ids: set[UUID]) -> dict[UUID, User]:
        if not user_ids:
            return {}
        rows = (
            (await self._session.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
        )
        return {row.id: row for row in rows}

    async def _extend_candidates(
        self,
        *,
        pool: list[DigestCandidate],
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[DigestCandidate]:
        candidates = list(pool)
        candidates.extend(
            await self._achievement_candidates(
                following_user_ids=following_user_ids,
                window_start=window_start,
                window_end=window_end,
            )
        )
        candidates.extend(
            await self._collection_milestone_candidates(
                following_user_ids=following_user_ids,
                window_start=window_start,
                window_end=window_end,
            )
        )
        return candidates

    async def _achievement_candidates(
        self,
        *,
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[DigestCandidate]:
        rows = (
            await self._session.execute(
                select(UserAchievement, Achievement, User)
                .join(Achievement, Achievement.id == UserAchievement.achievement_id)
                .join(User, User.id == UserAchievement.user_id)
                .where(UserAchievement.user_id.in_(following_user_ids))
                .where(UserAchievement.unlocked_at >= window_start)
                .where(UserAchievement.unlocked_at < window_end)
            )
        ).all()
        out: list[DigestCandidate] = []
        for unlock, achievement, author in rows:
            display = _format_friend_display(author)
            title = (achievement.title or achievement.slug).strip()
            out.append(
                DigestCandidate(
                    kind=DigestCandidateKind.author_activity_summary,
                    author_user_id=author.id,
                    author_display=display,
                    score=72.0,
                    occurred_at=unlock.unlocked_at,
                    line_html='',
                    entity_key=f'achievement:{unlock.id}',
                )
            )
            out[-1].line_html = f'{display} — ачивка «{title}»'
        return out

    async def _collection_milestone_candidates(
        self,
        *,
        following_user_ids: tuple[UUID, ...],
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[DigestCandidate]:
        rows = (
            await self._session.execute(
                select(
                    UserCard.user_id,
                    Collection.slug,
                    Collection.title,
                    func.count(UserCard.id),
                )
                .join(Film, Film.id == UserCard.film_id)
                .join(CollectionFilm, CollectionFilm.film_id == Film.id)
                .join(Collection, Collection.id == CollectionFilm.collection_id)
                .where(UserCard.user_id.in_(following_user_ids))
                .where(UserCard.is_planned.is_(False))
                .where(_completion_timestamp() >= window_start)
                .where(_completion_timestamp() < window_end)
                .group_by(UserCard.user_id, Collection.id, Collection.slug, Collection.title)
                .having(func.count(UserCard.id) >= 5)
            )
        ).all()
        out: list[DigestCandidate] = []
        for user_id, slug, title, count in rows:
            author = await self._session.get(User, user_id)
            if author is None:
                continue
            display = _format_friend_display(author)
            collection_title = str(title or slug)
            out.append(
                DigestCandidate(
                    kind=DigestCandidateKind.author_activity_summary,
                    author_user_id=author.id,
                    author_display=display,
                    score=68.0 + min(int(count), 10),
                    occurred_at=window_end,
                    line_html='',
                    entity_key=f'collection:{user_id}:{slug}',
                )
            )
            out[-1].line_html = f'{display} — +{int(count)} в «{collection_title}»'
        return out

    def _line_text_for_candidate(self, candidate: DigestCandidate) -> str | None:
        kind = candidate.kind
        if kind in (
            DigestCandidateKind.new_user_card,
            DigestCandidateKind.high_rating_card,
        ):
            title = candidate.film_title or 'фильм'
            rating = candidate.rating
            suffix = f' ({rating:.0f})' if rating is not None else ''
            return f'«{title}»{suffix}'
        if kind == DigestCandidateKind.new_feed_post:
            return candidate.post_snippet or 'новый пост'
        if kind == DigestCandidateKind.author_activity_summary:
            if candidate.entity_key.startswith('achievement:') or candidate.entity_key.startswith(
                'collection:'
            ):
                parts = candidate.line_html.split(' — ', maxsplit=1)
                return parts[1] if len(parts) == 2 else candidate.line_html
            card_count = candidate.activity_card_count or 0
            post_count = candidate.activity_post_count or 0
            total = card_count + post_count
            if total >= 2:
                genre_hint = ''
                if candidate.film_genres:
                    genre_hint = f' · топ жанр: {candidate.film_genres[0]}'
                return f'{total} оценки{genre_hint}'
        return None

    def _select_diverse(
        self,
        candidates: list[_FriendCandidate],
        *,
        limit: int,
    ) -> set[str]:
        by_author: dict[UUID, _FriendCandidate] = {}
        for candidate in sorted(candidates, key=lambda c: (-c.score, c.entity_key)):
            prev = by_author.get(candidate.author_user_id)
            if prev is None or candidate.score > prev.score:
                by_author[candidate.author_user_id] = candidate

        deduped = sorted(by_author.values(), key=lambda c: (-c.score, c.entity_key))
        selected: list[_FriendCandidate] = []
        for candidate in deduped:
            if len(selected) >= limit:
                break
            if any(item.author_user_id == candidate.author_user_id for item in selected):
                continue
            selected.append(candidate)
        return {item.entity_key for item in selected}
