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
    movie_card_id: int
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    rating: float


class MovieCardAnchorNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ListFollowingRatingsResult:
    """Строка зрителя (если есть своя карточка на тот же фильм) и подписки с оценками."""

    viewer_row: FollowingRatingRow | None
    items: list[FollowingRatingRow]


class ListFollowingRatingsForMovieCardService:
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
            raise MovieCardAnchorNotFoundError()

        film_id = anchor.film_id
        catalog_id = anchor.catalog_item_id
        owner_id = anchor.user_id

        viewer_row: FollowingRatingRow | None = None
        if viewer_user_id != owner_id:
            if film_id is not None:
                viewer_stmt = (
                    select(User, UserCard.rating, UserCard.id)
                    .join(UserCard, UserCard.user_id == User.id)
                    .where(UserCard.film_id == film_id)
                    .where(UserCard.user_id == viewer_user_id)
                    .order_by(UserCard.id.desc())
                    .limit(1)
                )
            elif catalog_id is not None:
                viewer_stmt = (
                    select(User, UserCard.rating, UserCard.id)
                    .join(UserCard, UserCard.user_id == User.id)
                    .where(UserCard.catalog_item_id == catalog_id)
                    .where(UserCard.user_id == viewer_user_id)
                    .order_by(UserCard.id.desc())
                    .limit(1)
                )
            else:
                viewer_stmt = None

            if viewer_stmt is not None:
                vr = (await self._session.execute(viewer_stmt)).one_or_none()
            else:
                vr = None
            if vr is not None:
                u, rating, movie_card_id = vr
                viewer_row = FollowingRatingRow(
                    user_id=u.id,
                    movie_card_id=int(movie_card_id),
                    profile_slug=u.profile_slug,
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    photo_url=u.photo_url,
                    display_name=u.display_name,
                    rating=float(rating),
                )

        if film_id is not None:
            match_on_film = UserCard.film_id == film_id
        elif catalog_id is not None:
            match_on_film = UserCard.catalog_item_id == catalog_id
        else:
            return ListFollowingRatingsResult(viewer_row=viewer_row, items=[])

        stmt = (
            select(User, UserCard.rating, UserCard.id)
            .join(UserCard, UserCard.user_id == User.id)
            .join(
                UserSubscription,
                (UserSubscription.following_user_id == UserCard.user_id)
                & (UserSubscription.follower_user_id == viewer_user_id),
            )
            .where(match_on_film)
            .where(UserCard.user_id != viewer_user_id)
            .where(UserCard.user_id != owner_id)
            .order_by(UserCard.rating.desc(), UserCard.id.desc())
            .limit(FOLLOWING_RATINGS_TOP_LIMIT)
        )
        rows = (await self._session.execute(stmt)).all()
        items = [
            FollowingRatingRow(
                user_id=u.id,
                movie_card_id=int(movie_card_id),
                profile_slug=u.profile_slug,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                photo_url=u.photo_url,
                display_name=u.display_name,
                rating=float(rating),
            )
            for u, rating, movie_card_id in rows
        ]
        return ListFollowingRatingsResult(viewer_row=viewer_row, items=items)
