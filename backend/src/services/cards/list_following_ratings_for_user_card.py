"""Подбор оценок того же фильма среди пользователей, на которых подписан зритель."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from services.cards.following_ratings_shared import (
    FOLLOWING_RATINGS_TOP_LIMIT,
    FollowingRatingRow,
    ListFollowingRatingsResult,
)
from services.cards.list_following_ratings_for_title import ListFollowingRatingsForTitleService

__all__ = [
    'FOLLOWING_RATINGS_TOP_LIMIT',
    'FollowingRatingRow',
    'ListFollowingRatingsForUserCardService',
    'ListFollowingRatingsResult',
    'UserCardAnchorNotFoundError',
]


class UserCardAnchorNotFoundError(Exception):
    pass


class ListFollowingRatingsForUserCardService:
    """Returns following ratings for an anchor user card via title service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._title_service = ListFollowingRatingsForTitleService.build(session)

    async def execute(
        self, viewer_user_id: UUID, anchor_card_id: int
    ) -> ListFollowingRatingsResult:
        anchor = (
            await self._session.execute(select(UserCard).where(UserCard.id == anchor_card_id))
        ).scalar_one_or_none()
        if anchor is None:
            raise UserCardAnchorNotFoundError()

        film_id = anchor.film_id
        catalog_id = anchor.catalog_item_id
        owner_id = anchor.user_id

        if film_id is None and catalog_id is None:
            return ListFollowingRatingsResult(viewer_row=None, items=[])

        # Title service requires exactly one anchor key. Kinopoisk-backed cards often
        # store both film_id and catalog_item_id; prefer film_id for friend matching.
        if film_id is not None:
            catalog_id = None

        try:
            result = await self._title_service.execute(
                viewer_user_id,
                film_id=film_id,
                catalog_item_id=catalog_id,
                exclude_user_id=owner_id,
            )
        except ListFollowingRatingsForTitleService.InvalidTitleRef:
            return ListFollowingRatingsResult(viewer_row=None, items=[])

        viewer_row = result.viewer_row
        if viewer_user_id == owner_id:
            viewer_row = None

        return ListFollowingRatingsResult(viewer_row=viewer_row, items=result.items)
