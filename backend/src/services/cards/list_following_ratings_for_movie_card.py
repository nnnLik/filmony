"""Подбор оценок того же фильма среди пользователей, на которых подписан зритель."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.user import User
from models.user_subscription import UserSubscription

FOLLOWING_RATINGS_TOP_LIMIT = 5


@dataclass(frozen=True, slots=True)
class FollowingRatingRow:
    user_id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None
    rating: float


class MovieCardAnchorNotFoundError(Exception):
    pass


class ListFollowingRatingsForMovieCardService:
    """Возвращает до N карточек того же фильма от людей, на которых зритель подписан.

    Автора открытой карточки и самого зрителя из списка убираем: у них оценка уже на экране или
    не показываем «себе среди друзей».
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, viewer_user_id: UUID, anchor_card_id: int) -> list[FollowingRatingRow]:
        anchor = (
            await self._session.execute(select(MovieCard).where(MovieCard.id == anchor_card_id))
        ).scalar_one_or_none()
        if anchor is None:
            raise MovieCardAnchorNotFoundError()

        film_id = anchor.film_id
        owner_id = anchor.user_id

        stmt = (
            select(User, MovieCard.rating)
            .join(MovieCard, MovieCard.user_id == User.id)
            .join(
                UserSubscription,
                (UserSubscription.following_user_id == MovieCard.user_id)
                & (UserSubscription.follower_user_id == viewer_user_id),
            )
            .where(MovieCard.film_id == film_id)
            .where(MovieCard.user_id != viewer_user_id)
            .where(MovieCard.user_id != owner_id)
            .order_by(MovieCard.rating.desc(), MovieCard.id.desc())
            .limit(FOLLOWING_RATINGS_TOP_LIMIT)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            FollowingRatingRow(
                user_id=u.id,
                profile_slug=u.profile_slug,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                photo_url=u.photo_url,
                display_name=u.display_name,
                rating=float(rating),
            )
            for u, rating in rows
        ]
