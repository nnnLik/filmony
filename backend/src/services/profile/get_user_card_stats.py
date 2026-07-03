from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from math import floor
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.film import Film
from models.user_card import UserCard
from models.user_card_category import UserCardCategory

UNCATEGORIZED_SHELF_NAME = 'Без полки'
ACTIVITY_WINDOW_DAYS = 180


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
class TagTasteItem:
    tag: str
    count: int
    average_rating: float


@dataclass(frozen=True, slots=True)
class ProfileInsights:
    activity_total_180d: int
    dominant_company: str | None
    dominant_mood_after: str | None
    top_tag: str | None


@dataclass(frozen=True, slots=True)
class CategoryDistributionItem:
    category_id: int | None
    name: str
    count: int


@dataclass(frozen=True, slots=True)
class ActivityDistributionItem:
    date: dt.date
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
class UserCardStats:
    total_movies: int
    average_rating: float
    rating_distribution: list[RatingDistributionItem]
    year_distribution: list[YearDistributionItem]
    popular_tags: list[TagDistributionItem]
    tag_taste: list[TagTasteItem]
    insights: ProfileInsights
    watch_with_distribution: list[ValueDistributionItem]
    mood_after_distribution: list[ValueDistributionItem]
    category_distribution: list[CategoryDistributionItem]
    top_movies: list[ProfileMovieStatsItem]
    worst_movies: list[ProfileMovieStatsItem]
    activity_distribution: list[ActivityDistributionItem]
    activity_start: dt.date
    activity_end: dt.date


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


@dataclass
class GetUserCardStatsService:
    """Loads per-user card aggregates for profile stats (ratings, tags, shelves, top/worst)."""

    _session: AsyncSession

    class InvalidCategoryFilter(Exception):
        """activity_category_id does not belong to the profile user."""

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        user_id: UUID,
        *,
        activity_category_id: int | None = None,
    ) -> UserCardStats:
        if activity_category_id is not None:
            owns = (
                await self._session.execute(
                    select(UserCardCategory.id).where(
                        UserCardCategory.id == activity_category_id,
                        UserCardCategory.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if owns is None:
                raise self.InvalidCategoryFilter

        activity_end = dt.datetime.now(dt.UTC).date()
        activity_start = activity_end - dt.timedelta(days=ACTIVITY_WINDOW_DAYS - 1)

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
                    UserCardCategory.id.label('shelf_category_id'),
                    UserCardCategory.name.label('shelf_category_name'),
                )
                .join(Film, Film.id == UserCard.film_id)
                .outerjoin(
                    UserCardCategory,
                    (UserCardCategory.id == UserCard.category_id)
                    & (UserCardCategory.user_id == UserCard.user_id),
                )
                .where(UserCard.user_id == user_id, UserCard.is_planned.is_(False))
            )
        ).all()

        total_movies = len(card_rows)
        rating_counts = dict.fromkeys(range(1, 11), 0)
        rating_sum = 0.0
        year_counts: dict[int, int] = {}
        company_counts: dict[str, int] = {}
        mood_after_counts: dict[str, int] = {}
        category_counts: dict[int | None, int] = {}
        category_names: dict[int, str] = {}
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
            if row.shelf_category_id is not None:
                cid = int(row.shelf_category_id)
                category_names[cid] = str(row.shelf_category_name)
                category_counts[cid] = category_counts.get(cid, 0) + 1
            else:
                category_counts[None] = category_counts.get(None, 0) + 1
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
        category_distribution = [
            CategoryDistributionItem(
                category_id=None,
                name=UNCATEGORIZED_SHELF_NAME,
                count=count,
            )
            if category_id is None
            else CategoryDistributionItem(
                category_id=category_id,
                name=category_names[category_id],
                count=count,
            )
            for category_id, count in sorted(
                category_counts.items(),
                key=lambda item: (-item[1], item[0] is not None, item[0] or 0),
            )
        ]

        tag_rows = (
            await self._session.execute(
                select(CardTag.tag, func.count(CardTag.id))
                .join(UserCard, UserCard.id == CardTag.card_id)
                .where(UserCard.user_id == user_id, UserCard.is_planned.is_(False))
                .group_by(CardTag.tag)
                .order_by(desc(func.count(CardTag.id)), CardTag.tag)
                .limit(10)
            )
        ).all()
        popular_tags = [TagDistributionItem(tag=tag, count=int(count)) for tag, count in tag_rows]

        tag_taste_rows = (
            await self._session.execute(
                select(
                    CardTag.tag,
                    func.count(CardTag.id),
                    func.avg(UserCard.rating),
                )
                .join(UserCard, UserCard.id == CardTag.card_id)
                .where(UserCard.user_id == user_id, UserCard.is_planned.is_(False))
                .group_by(CardTag.tag)
                .order_by(desc(func.count(CardTag.id)), CardTag.tag)
                .limit(10)
            )
        ).all()
        tag_taste = [
            TagTasteItem(
                tag=tag,
                count=int(count),
                average_rating=round(float(avg_rating), 1),
            )
            for tag, count, avg_rating in tag_taste_rows
        ]

        sorted_by_top = sorted(movies, key=lambda item: (-item.rating, item.card_id))
        sorted_by_worst = sorted(movies, key=lambda item: (item.rating, item.card_id))

        activity_distribution = await self._load_activity_distribution(
            user_id=user_id,
            activity_start=activity_start,
            activity_end=activity_end,
            activity_category_id=activity_category_id,
        )

        activity_total_180d = sum(item.count for item in activity_distribution)
        dominant_company = watch_with_distribution[0].value if watch_with_distribution else None
        dominant_mood_after = mood_after_distribution[0].value if mood_after_distribution else None
        top_tag = tag_taste[0].tag if tag_taste else None
        insights = ProfileInsights(
            activity_total_180d=activity_total_180d,
            dominant_company=dominant_company,
            dominant_mood_after=dominant_mood_after,
            top_tag=top_tag,
        )

        return UserCardStats(
            total_movies=total_movies,
            average_rating=average_rating,
            rating_distribution=rating_distribution,
            year_distribution=year_distribution,
            popular_tags=popular_tags,
            tag_taste=tag_taste,
            insights=insights,
            watch_with_distribution=watch_with_distribution,
            mood_after_distribution=mood_after_distribution,
            category_distribution=category_distribution,
            top_movies=sorted_by_top[:5],
            worst_movies=sorted_by_worst[:5],
            activity_distribution=activity_distribution,
            activity_start=activity_start,
            activity_end=activity_end,
        )

    async def _load_activity_distribution(
        self,
        *,
        user_id: UUID,
        activity_start: dt.date,
        activity_end: dt.date,
        activity_category_id: int | None,
    ) -> list[ActivityDistributionItem]:
        completion = _completion_timestamp()
        day_col = func.date(completion).label('day')
        query = (
            select(day_col, func.count(UserCard.id))
            .where(
                UserCard.user_id == user_id,
                UserCard.is_planned.is_(False),
                func.date(completion) >= activity_start,
                func.date(completion) <= activity_end,
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        if activity_category_id is not None:
            query = query.where(UserCard.category_id == activity_category_id)

        rows = (await self._session.execute(query)).all()
        return [ActivityDistributionItem(date=day, count=int(count)) for day, count in rows]
