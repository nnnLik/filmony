"""Подбор оценок того же фильма среди пользователей, на которых подписан зритель."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription

FOLLOWING_RATINGS_TOP_LIMIT = 5


@dataclass(frozen=True, slots=True)
class FollowingRatingRow:
    user_id: UUID
    user_card_id: int
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    is_planned: bool
    rating: float | None


class UserCardAnchorNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ListFollowingRatingsResult:
    """Строка зрителя (если есть своя карточка на тот же фильм) и подписки с оценками."""

    viewer_row: FollowingRatingRow | None
    items: list[FollowingRatingRow]


class ListFollowingRatingsForUserCardService:
    """Возвращает оценки того же фильма: опционально карточку зрителя и до N подписок.

    Подписки — пользователи, на которых зритель подписан, с карточкой на тот же фильм; из этого
    списка исключаются автор открытой карточки и сам зритель (чтобы не дублировать строки).

    Если зритель открыл чужую карточку и у него в библиотеке есть оценка этого тайтла, она
    возвращается отдельно в ``viewer_row`` (на экране автор уже показан крупно, зритель — нет).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

        viewer_row: FollowingRatingRow | None = None
        if viewer_user_id != owner_id:
            if film_id is not None:
                viewer_stmt = (
                    select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
                    .join(UserCard, UserCard.user_id == User.id)
                    .where(UserCard.film_id == film_id)
                    .where(UserCard.user_id == viewer_user_id)
                    .order_by(UserCard.id.desc())
                )
            elif catalog_id is not None:
                viewer_stmt = (
                    select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
                    .join(UserCard, UserCard.user_id == User.id)
                    .where(UserCard.catalog_item_id == catalog_id)
                    .where(UserCard.user_id == viewer_user_id)
                    .order_by(UserCard.id.desc())
                )
            else:
                viewer_stmt = None

            if viewer_stmt is not None:
                viewer_rows = (await self._session.execute(viewer_stmt)).all()
            else:
                viewer_rows = []
            picked = _pick_viewer_card_row(viewer_rows)
            if picked is not None:
                u, rating, user_card_id, is_planned = picked
                viewer_row = _following_rating_row_from_parts(
                    u=u,
                    user_card_id=int(user_card_id),
                    rating=float(rating),
                    is_planned=bool(is_planned),
                )

        if film_id is not None:
            match_on_film = UserCard.film_id == film_id
        elif catalog_id is not None:
            match_on_film = UserCard.catalog_item_id == catalog_id
        else:
            return ListFollowingRatingsResult(viewer_row=viewer_row, items=[])

        stmt = (
            select(User, UserCard.rating, UserCard.id, UserCard.is_planned)
            .join(UserCard, UserCard.user_id == User.id)
            .join(
                UserSubscription,
                (UserSubscription.following_user_id == UserCard.user_id)
                & (UserSubscription.follower_user_id == viewer_user_id),
            )
            .where(match_on_film)
            .where(UserCard.user_id != viewer_user_id)
            .where(UserCard.user_id != owner_id)
            .where(UserCard.is_planned.is_(False))
            .where(UserCard.rating >= 1)
            .order_by(UserCard.rating.desc(), UserCard.id.desc())
            .limit(FOLLOWING_RATINGS_TOP_LIMIT)
        )
        rows = (await self._session.execute(stmt)).all()
        items = [
            _following_rating_row_from_parts(
                u=u,
                user_card_id=int(user_card_id),
                rating=float(rating),
                is_planned=bool(is_planned),
            )
            for u, rating, user_card_id, is_planned in rows
        ]
        return ListFollowingRatingsResult(viewer_row=viewer_row, items=items)


def _pick_viewer_card_row(
    rows: list[tuple[User, float, int, bool]],
) -> tuple[User, float, int, bool] | None:
    """Prefer rated card over planned-only snippet for the same title."""
    for u, rating, user_card_id, is_planned in rows:
        if not is_planned and float(rating) >= 1:
            return u, rating, user_card_id, is_planned
    for u, rating, user_card_id, is_planned in rows:
        if is_planned:
            return u, rating, user_card_id, is_planned
    return None


def _following_rating_row_from_parts(
    *,
    u: User,
    user_card_id: int,
    rating: float,
    is_planned: bool,
) -> FollowingRatingRow:
    planned_only = is_planned or rating < 1
    return FollowingRatingRow(
        user_id=u.id,
        user_card_id=user_card_id,
        profile_slug=u.profile_slug,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        photo_url=u.photo_url,
        display_name=u.display_name,
        is_planned=planned_only,
        rating=None if planned_only else rating,
    )
