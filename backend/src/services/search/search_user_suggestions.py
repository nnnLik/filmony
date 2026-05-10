from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import exists, not_, select
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from models.movie_card import MovieCard
from models.user import User
from models.user_subscription import UserSubscription


@dataclass(frozen=True, slots=True)
class SuggestedUserProfile:
    """Public-facing fields for a suggested profile row."""

    id: UUID
    profile_slug: str
    username: str | None
    display_name: str | None
    photo_url: str | None
    movie_cards_count: int = 0
    average_rating: float | None = None


@dataclass(frozen=True, slots=True)
class SearchUserSuggestionsResult:
    mutual_circle: list[SuggestedUserProfile]
    popular_authors: list[SuggestedUserProfile]
    random_with_cards: list[SuggestedUserProfile]


@dataclass
class SearchUserSuggestionsService:
    """Builds three disjoint suggestion lists: mutual subscriptions overlap, weekly
    popular authors by new cards, and random users with cards. Each user appears at
    most once across lists (mutual first, then popular, then random).
    """

    _session: AsyncSession

    MUTUAL_LIMIT: int = 3
    POPULAR_LIMIT: int = 3
    RANDOM_LIMIT: int = 3

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, viewer_user_id: UUID) -> SearchUserSuggestionsResult:
        followee_ids = await self._followee_user_ids(viewer_user_id)
        exclude_base: set[UUID] = {viewer_user_id, *followee_ids}

        mutual = await self._mutual_circle(viewer_user_id, self.MUTUAL_LIMIT)
        used: set[UUID] = exclude_base | {u.id for u in mutual}

        popular = await self._popular_authors(
            viewer_user_id,
            self.POPULAR_LIMIT,
            exclude_user_ids=used,
        )
        used |= {u.id for u in popular}

        random_users = await self._random_with_cards(
            viewer_user_id,
            self.RANDOM_LIMIT,
            exclude_user_ids=used,
        )

        return SearchUserSuggestionsResult(
            mutual_circle=mutual,
            popular_authors=popular,
            random_with_cards=random_users,
        )

    async def _followee_user_ids(self, viewer_user_id: UUID) -> set[UUID]:
        stmt = select(UserSubscription.following_user_id).where(
            UserSubscription.follower_user_id == viewer_user_id
        )
        res = await self._session.execute(stmt)
        return {row[0] for row in res.all()}

    async def _mutual_circle(self, viewer_user_id: UUID, limit: int) -> list[SuggestedUserProfile]:
        cand_sub = aliased(UserSubscription)

        following_ids = select(UserSubscription.following_user_id).where(
            UserSubscription.follower_user_id == viewer_user_id
        )

        viewer_already_follows_candidate = exists(
            select(1)
            .select_from(UserSubscription)
            .where(
                UserSubscription.follower_user_id == viewer_user_id,
                UserSubscription.following_user_id == cand_sub.follower_user_id,
            )
        )

        overlap_stmt = (
            select(cand_sub.follower_user_id, sa_func.count().label('overlap'))
            .where(cand_sub.following_user_id.in_(following_ids))
            .where(cand_sub.follower_user_id != viewer_user_id)
            .where(not_(viewer_already_follows_candidate))
            .group_by(cand_sub.follower_user_id)
            .order_by(sa_func.count().desc(), cand_sub.follower_user_id.asc())
            .limit(limit)
        )

        overlap_result = await self._session.execute(overlap_stmt)
        pairs = overlap_result.all()
        if not pairs:
            return []

        user_ids = [row[0] for row in pairs]
        stats = await self._movie_card_stats_for_users(user_ids)
        return await self._users_by_ids_ordered(user_ids, stats)

    async def _popular_authors(
        self,
        viewer_user_id: UUID,
        limit: int,
        *,
        exclude_user_ids: set[UUID],
    ) -> list[SuggestedUserProfile]:
        # DB `created_at` is naive UTC (see CreatedAtMixin); bind naive for asyncpg.
        since = (dt.datetime.now(dt.UTC) - dt.timedelta(days=7)).replace(tzinfo=None)

        stmt = (
            select(MovieCard.user_id, sa_func.count().label('cnt'))
            .where(MovieCard.created_at >= since)
            .where(MovieCard.user_id != viewer_user_id)
        )
        if exclude_user_ids:
            stmt = stmt.where(MovieCard.user_id.notin_(exclude_user_ids))

        stmt = (
            stmt.group_by(MovieCard.user_id)
            .order_by(sa_func.count().desc(), MovieCard.user_id.asc())
            .limit(limit)
        )

        res = await self._session.execute(stmt)
        rows = res.all()
        if not rows:
            return []

        user_ids = [row[0] for row in rows]
        stats = await self._movie_card_stats_for_users(user_ids)
        return await self._users_by_ids_ordered(user_ids, stats)

    async def _random_with_cards(
        self,
        viewer_user_id: UUID,
        limit: int,
        *,
        exclude_user_ids: set[UUID],
    ) -> list[SuggestedUserProfile]:
        has_card = select(1).select_from(MovieCard).where(MovieCard.user_id == User.id).exists()

        stmt = select(User.id).where(has_card).where(User.id != viewer_user_id)
        if exclude_user_ids:
            stmt = stmt.where(User.id.notin_(exclude_user_ids))

        stmt = stmt.order_by(sa_func.random()).limit(limit)

        res = await self._session.execute(stmt)
        ids = [row[0] for row in res.all()]
        if not ids:
            return []

        stats = await self._movie_card_stats_for_users(ids)
        return await self._users_by_ids_ordered(ids, stats)

    async def _movie_card_stats_for_users(
        self, user_ids: list[UUID]
    ) -> dict[UUID, tuple[int, float | None]]:
        if not user_ids:
            return {}
        stmt = (
            select(MovieCard.user_id, sa_func.count().label('cnt'), sa_func.avg(MovieCard.rating))
            .where(MovieCard.user_id.in_(user_ids))
            .group_by(MovieCard.user_id)
        )
        res = await self._session.execute(stmt)
        out: dict[UUID, tuple[int, float | None]] = {}
        for uid, cnt, avg in res.all():
            n = int(cnt)
            if n <= 0:
                out[uid] = (0, None)
            else:
                out[uid] = (n, round(float(avg), 2) if avg is not None else None)
        return out

    async def _users_by_ids_ordered(
        self,
        user_ids: list[UUID],
        stats: dict[UUID, tuple[int, float | None]],
    ) -> list[SuggestedUserProfile]:
        if not user_ids:
            return []

        stmt = select(User).where(User.id.in_(user_ids))
        res = await self._session.execute(stmt)
        by_id = {u.id: u for u in res.scalars().all()}
        out: list[SuggestedUserProfile] = []
        for uid in user_ids:
            u = by_id.get(uid)
            if u is None:
                continue
            cnt, avg = stats.get(uid, (0, None))
            out.append(
                SuggestedUserProfile(
                    id=u.id,
                    profile_slug=u.profile_slug,
                    username=u.username,
                    display_name=u.display_name,
                    photo_url=u.photo_url,
                    movie_cards_count=cnt,
                    average_rating=avg,
                )
            )
        return out
