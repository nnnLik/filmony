"""Подбор оценок подписок для тайтла (film_id или catalog_item_id)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from services.cards.following_ratings_shared import (
    FOLLOWING_RATINGS_TOP_LIMIT,
    FollowingRatingRow,
    ListFollowingRatingsResult,
    following_rating_row_from_parts,
    pick_viewer_card_row,
)


@dataclass
class ListFollowingRatingsForTitleService:
    """Returns following users' ratings for a film or catalog item title."""

    _session: AsyncSession

    class InvalidTitleRef(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        viewer_user_id: UUID,
        *,
        film_id: int | None = None,
        catalog_item_id: int | None = None,
        exclude_user_id: UUID | None = None,
    ) -> ListFollowingRatingsResult:
        has_film = film_id is not None
        has_catalog = catalog_item_id is not None
        if has_film == has_catalog:
            raise self.InvalidTitleRef

        viewer_row: FollowingRatingRow | None = None
        if exclude_user_id is None or viewer_user_id != exclude_user_id:
            viewer_row = await self._load_viewer_row(
                viewer_user_id,
                film_id=film_id,
                catalog_item_id=catalog_item_id,
            )

        if film_id is not None:
            match_on_title = UserCard.film_id == film_id
        else:
            match_on_title = UserCard.catalog_item_id == catalog_item_id

        stmt = (
            select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
            .join(UserCard, UserCard.user_id == User.id)
            .join(
                UserSubscription,
                (UserSubscription.following_user_id == UserCard.user_id)
                & (UserSubscription.follower_user_id == viewer_user_id),
            )
            .where(match_on_title)
            .where(UserCard.user_id != viewer_user_id)
            .where(UserCard.is_planned.is_(False))
            .where(UserCard.rating >= 1)
            .order_by(UserCard.rating.desc(), UserCard.id.desc())
            .limit(FOLLOWING_RATINGS_TOP_LIMIT)
        )
        if exclude_user_id is not None:
            stmt = stmt.where(UserCard.user_id != exclude_user_id)

        rows = (await self._session.execute(stmt)).all()
        items = [
            following_rating_row_from_parts(
                u=u,
                user_card_id=int(user_card_id),
                rating=float(rating),
                is_planned=bool(is_planned),
            )
            for u, rating, user_card_id, is_planned in rows
        ]
        return ListFollowingRatingsResult(viewer_row=viewer_row, items=items)

    async def _load_viewer_row(
        self,
        viewer_user_id: UUID,
        *,
        film_id: int | None,
        catalog_item_id: int | None,
    ) -> FollowingRatingRow | None:
        if film_id is not None:
            viewer_stmt = (
                select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
                .join(UserCard, UserCard.user_id == User.id)
                .where(UserCard.film_id == film_id)
                .where(UserCard.user_id == viewer_user_id)
                .order_by(UserCard.id.desc())
            )
        else:
            viewer_stmt = (
                select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
                .join(UserCard, UserCard.user_id == User.id)
                .where(UserCard.catalog_item_id == catalog_item_id)
                .where(UserCard.user_id == viewer_user_id)
                .order_by(UserCard.id.desc())
            )

        viewer_rows = (await self._session.execute(viewer_stmt)).all()
        picked = pick_viewer_card_row(viewer_rows)
        if picked is None:
            return None
        u, rating, user_card_id, is_planned = picked
        return following_rating_row_from_parts(
            u=u,
            user_card_id=int(user_card_id),
            rating=float(rating),
            is_planned=bool(is_planned),
        )
