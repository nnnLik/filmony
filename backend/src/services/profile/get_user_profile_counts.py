from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.user_subscription import UserSubscription
from models.user_watchlist_film import UserWatchlistFilm


@dataclass(frozen=True, slots=True)
class UserProfileCounts:
    movie_cards: int
    watchlist_films: int
    favorites: int
    friends: int
    followers_count: int
    following_count: int


class GetUserProfileCountsService:
    """Aggregate counts for profile headers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID) -> UserProfileCounts:
        movie_cards = (
            select(func.count(MovieCard.id)).where(MovieCard.user_id == user_id).scalar_subquery()
        )
        favorites = (
            select(func.count(MovieCard.id))
            .where(MovieCard.user_id == user_id, MovieCard.is_favorite.is_(True))
            .scalar_subquery()
        )
        watchlist_films = (
            select(func.count(UserWatchlistFilm.id))
            .where(UserWatchlistFilm.user_id == user_id)
            .scalar_subquery()
        )
        followers_count = (
            select(func.count(UserSubscription.id))
            .where(UserSubscription.following_user_id == user_id)
            .scalar_subquery()
        )
        following_count = (
            select(func.count(UserSubscription.id))
            .where(UserSubscription.follower_user_id == user_id)
            .scalar_subquery()
        )
        row = (
            await self._session.execute(
                select(movie_cards, watchlist_films, favorites, followers_count, following_count)
            )
        ).one()
        return UserProfileCounts(
            movie_cards=int(row[0]),
            watchlist_films=int(row[1]),
            favorites=int(row[2]),
            friends=0,
            followers_count=int(row[3]),
            following_count=int(row[4]),
        )
