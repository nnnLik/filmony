from __future__ import annotations

from dataclasses import dataclass
from math import floor
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.film import Film
from models.user_card import UserCard


@dataclass(frozen=True, slots=True)
class RatingDistributionItem:
    rating: int
    count: int


@dataclass(frozen=True, slots=True)
class YearDistributionItem:
    year: int
    count: int


@dataclass(frozen=True, slots=True)
class ValueDistributionItem:
    value: str
    count: int


@dataclass(frozen=True, slots=True)
class TagDistributionItem:
    tag: str
    count: int


@dataclass(frozen=True, slots=True)
class ProfileMovieStatsItem:
    card_id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float


@dataclass(frozen=True, slots=True)
class UserMovieCardStats:
    total_movies: int
    average_rating: float
    rating_distribution: list[RatingDistributionItem]
    year_distribution: list[YearDistributionItem]
    popular_tags: list[TagDistributionItem]
    watch_with_distribution: list[ValueDistributionItem]
    mood_after_distribution: list[ValueDistributionItem]
    top_movies: list[ProfileMovieStatsItem]
    worst_movies: list[ProfileMovieStatsItem]


class GetUserMovieCardStatsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID) -> UserMovieCardStats:
        card_rows = (
            await self._session.execute(
                select(
                    UserCard.id,
                    UserCard.film_id,
                    UserCard.rating,
                    UserCard.company,
                    UserCard.mood_after,
                    Film.title,
                    Film.year,
                    Film.poster_url,
                )
                .join(Film, Film.id == UserCard.film_id)
                .where(UserCard.user_id == user_id)
            )
        ).all()

        total_movies = len(card_rows)
        rating_counts = dict.fromkeys(range(1, 11), 0)
        rating_sum = 0.0
        year_counts: dict[int, int] = {}
        company_counts: dict[str, int] = {}
        mood_after_counts: dict[str, int] = {}
        movies: list[ProfileMovieStatsItem] = []

        for row in card_rows:
            rating_value = float(row.rating)
            rating_sum += rating_value
            rating_bucket = max(1, min(10, floor(rating_value + 0.5)))
            rating_counts[rating_bucket] += 1
            if row.year is not None:
                year_counts[int(row.year)] = year_counts.get(int(row.year), 0) + 1
            company_counts[row.company] = company_counts.get(row.company, 0) + 1
            mood_after_counts[row.mood_after] = mood_after_counts.get(row.mood_after, 0) + 1
            movies.append(
                ProfileMovieStatsItem(
                    card_id=int(row.id),
                    film_id=int(row.film_id),
                    film_title=row.title,
                    film_year=row.year,
                    film_poster_url=row.poster_url,
                    rating=rating_value,
                )
            )

        average_rating = round(rating_sum / total_movies, 1) if total_movies > 0 else 0.0
        rating_distribution = [
            RatingDistributionItem(rating=score, count=rating_counts[score])
            for score in range(1, 11)
        ]
        year_distribution = [
            YearDistributionItem(year=year, count=count)
            for year, count in sorted(year_counts.items(), key=lambda item: item[0], reverse=True)
        ]
        watch_with_distribution = [
            ValueDistributionItem(value=value, count=count)
            for value, count in sorted(company_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        mood_after_distribution = [
            ValueDistributionItem(value=value, count=count)
            for value, count in sorted(
                mood_after_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ]

        tag_rows = (
            await self._session.execute(
                select(CardTag.tag, func.count(CardTag.id))
                .join(UserCard, UserCard.id == CardTag.card_id)
                .where(UserCard.user_id == user_id)
                .group_by(CardTag.tag)
                .order_by(desc(func.count(CardTag.id)), CardTag.tag)
                .limit(10)
            )
        ).all()
        popular_tags = [TagDistributionItem(tag=tag, count=int(count)) for tag, count in tag_rows]

        sorted_by_top = sorted(movies, key=lambda item: (-item.rating, item.card_id))
        sorted_by_worst = sorted(movies, key=lambda item: (item.rating, item.card_id))

        return UserMovieCardStats(
            total_movies=total_movies,
            average_rating=average_rating,
            rating_distribution=rating_distribution,
            year_distribution=year_distribution,
            popular_tags=popular_tags,
            watch_with_distribution=watch_with_distribution,
            mood_after_distribution=mood_after_distribution,
            top_movies=sorted_by_top[:5],
            worst_movies=sorted_by_worst[:5],
        )
