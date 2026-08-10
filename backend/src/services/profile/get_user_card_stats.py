from __future__ import annotations

import datetime as dt
import heapq
from dataclasses import dataclass
from math import floor
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user_card import UserCard
from models.user_card_category import UserCardCategory
from services.directors.get_director_summary import _rated_card_filters
from services.franchises.franchise_label import franchise_fallback_label, resolve_franchise_labels

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
    top_director_kinopoisk_id: int | None
    top_director_name: str | None
    top_director_count: int
    top_actor_kinopoisk_id: int | None
    top_actor_name: str | None
    top_actor_count: int
    top_franchise_key: str | None
    top_franchise_label: str | None
    top_franchise_count: int


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
class GenreDistributionItem:
    genre: str
    count: int


@dataclass(frozen=True, slots=True)
class DirectorDistributionItem:
    kinopoisk_id: int
    name: str
    count: int


@dataclass(frozen=True, slots=True)
class ActorDistributionItem:
    kinopoisk_id: int
    name: str
    poster_url: str | None
    count: int


@dataclass(frozen=True, slots=True)
class FranchiseDistributionItem:
    franchise_key: str
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class UserCardStats:
    total_movies: int
    average_rating: float
    rating_distribution: list[RatingDistributionItem]
    year_distribution: list[YearDistributionItem]
    rated_year_distribution: list[YearDistributionItem]
    genre_distribution: list[GenreDistributionItem]
    director_distribution: list[DirectorDistributionItem]
    actor_distribution: list[ActorDistributionItem]
    franchise_distribution: list[FranchiseDistributionItem]
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
                    UserCard.completed_at,
                    UserCard.created_at,
                    Film.title,
                    Film.year,
                    Film.poster_url,
                    Film.genres,
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                    Film.franchise_key,
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
        rated_year_counts: dict[int, int] = {}
        company_counts: dict[str, int] = {}
        mood_after_counts: dict[str, int] = {}
        category_counts: dict[int | None, int] = {}
        category_names: dict[int, str] = {}
        genre_counts: dict[str, int] = {}
        director_counts: dict[int, tuple[str, int]] = {}
        franchise_counts: dict[str, int] = {}
        movies: list[ProfileMovieStatsItem] = []

        for row in card_rows:
            rating_value = float(row.rating)
            rating_sum += rating_value
            rating_bucket = max(1, min(10, floor(rating_value + 0.5)))
            rating_counts[rating_bucket] += 1
            if row.year is not None:
                year_counts[int(row.year)] = year_counts.get(int(row.year), 0) + 1
            for genre_name in row.genres or []:
                label = str(genre_name).strip()
                if label:
                    genre_counts[label] = genre_counts.get(label, 0) + 1
            if row.primary_director_kinopoisk_id is not None:
                director_id = int(row.primary_director_kinopoisk_id)
                director_name = (
                    str(row.primary_director_name or '').strip() or f'Режиссёр #{director_id}'
                )
                existing_name, existing_count = director_counts.get(director_id, (director_name, 0))
                director_counts[director_id] = (existing_name or director_name, existing_count + 1)
            franchise_key = str(row.franchise_key or '').strip()
            if franchise_key != '':
                franchise_counts[franchise_key] = franchise_counts.get(franchise_key, 0) + 1
            rated_at = row.completed_at or row.created_at
            rated_year = rated_at.year
            rated_year_counts[rated_year] = rated_year_counts.get(rated_year, 0) + 1
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
            RatingDistributionItem(rating=score, count=count)
            for score, count in rating_counts.items()
            if count > 0
        ]
        year_distribution = [
            YearDistributionItem(year=year, count=count)
            for year, count in sorted(year_counts.items(), key=lambda item: item[0], reverse=True)
        ]
        rated_year_distribution = [
            YearDistributionItem(year=year, count=count)
            for year, count in sorted(
                rated_year_counts.items(), key=lambda item: item[0], reverse=True
            )
        ]
        genre_distribution = [
            GenreDistributionItem(genre=genre, count=count)
            for genre, count in sorted(genre_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        director_distribution = [
            DirectorDistributionItem(kinopoisk_id=kinopoisk_id, name=name, count=count)
            for kinopoisk_id, (name, count) in sorted(
                director_counts.items(),
                key=lambda item: (-item[1][1], item[1][0]),
            )[:20]
        ]
        rated_cards = (
            select(
                UserCard.id.label('card_id'),
                UserCard.film_id,
            ).where(UserCard.user_id == user_id, *_rated_card_filters())
        ).cte('rated_cards')
        actor_counts = (
            select(
                FilmActor.person_id,
                func.count(rated_cards.c.card_id).label('actor_count'),
            )
            .select_from(rated_cards)
            .join(FilmActor, FilmActor.film_id == rated_cards.c.film_id)
            .group_by(FilmActor.person_id)
        ).subquery('actor_counts')
        actor_rows = (
            await self._session.execute(
                select(
                    Person.kinopoisk_id,
                    Person.name,
                    Person.poster_url,
                    actor_counts.c.actor_count,
                )
                .select_from(actor_counts)
                .join(Person, Person.id == actor_counts.c.person_id)
                .order_by(
                    desc(actor_counts.c.actor_count),
                    Person.name,
                    Person.kinopoisk_id,
                )
                .limit(20)
            )
        ).all()
        actor_distribution = [
            ActorDistributionItem(
                kinopoisk_id=int(kinopoisk_id),
                name=str(name),
                poster_url=poster_url,
                count=int(count),
            )
            for kinopoisk_id, name, poster_url, count in actor_rows
        ]
        sorted_franchise_items = sorted(
            franchise_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        franchise_labels = await resolve_franchise_labels(
            self._session,
            (franchise_key for franchise_key, _ in sorted_franchise_items),
        )
        franchise_distribution = [
            FranchiseDistributionItem(
                franchise_key=franchise_key,
                label=franchise_labels.get(
                    franchise_key,
                    franchise_fallback_label(franchise_key),
                ),
                count=count,
            )
            for franchise_key, count in sorted_franchise_items
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
        popular_tags = [
            TagDistributionItem(tag=tag, count=int(count)) for tag, count, _ in tag_rows
        ]
        tag_taste = [
            TagTasteItem(
                tag=tag,
                count=int(count),
                average_rating=round(float(avg_rating), 1),
            )
            for tag, count, avg_rating in tag_rows
        ]

        top_movies = heapq.nlargest(
            5,
            movies,
            key=lambda item: (item.rating, -item.card_id),
        )
        worst_movies = heapq.nsmallest(5, movies, key=lambda item: (item.rating, item.card_id))

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
        top_director = director_distribution[0] if director_distribution else None
        top_actor = actor_distribution[0] if actor_distribution else None
        top_franchise = franchise_distribution[0] if franchise_distribution else None
        insights = ProfileInsights(
            activity_total_180d=activity_total_180d,
            dominant_company=dominant_company,
            dominant_mood_after=dominant_mood_after,
            top_tag=top_tag,
            top_director_kinopoisk_id=top_director.kinopoisk_id if top_director else None,
            top_director_name=top_director.name if top_director else None,
            top_director_count=top_director.count if top_director else 0,
            top_actor_kinopoisk_id=top_actor.kinopoisk_id if top_actor else None,
            top_actor_name=top_actor.name if top_actor else None,
            top_actor_count=top_actor.count if top_actor else 0,
            top_franchise_key=top_franchise.franchise_key if top_franchise else None,
            top_franchise_label=top_franchise.label if top_franchise else None,
            top_franchise_count=top_franchise.count if top_franchise else 0,
        )

        return UserCardStats(
            total_movies=total_movies,
            average_rating=average_rating,
            rating_distribution=rating_distribution,
            year_distribution=year_distribution,
            rated_year_distribution=rated_year_distribution,
            genre_distribution=genre_distribution,
            director_distribution=director_distribution,
            actor_distribution=actor_distribution,
            franchise_distribution=franchise_distribution,
            popular_tags=popular_tags,
            tag_taste=tag_taste,
            insights=insights,
            watch_with_distribution=watch_with_distribution,
            mood_after_distribution=mood_after_distribution,
            category_distribution=category_distribution,
            top_movies=top_movies,
            worst_movies=worst_movies,
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
        range_start = dt.datetime.combine(activity_start, dt.time.min, tzinfo=dt.UTC)
        range_end_exclusive = dt.datetime.combine(
            activity_end + dt.timedelta(days=1),
            dt.time.min,
            tzinfo=dt.UTC,
        )
        query = (
            select(day_col, func.count(UserCard.id))
            .where(
                UserCard.user_id == user_id,
                UserCard.is_planned.is_(False),
                completion >= range_start,
                completion < range_end_exclusive,
            )
            .group_by(day_col)
            .order_by(day_col)
        )
        if activity_category_id is not None:
            query = query.where(UserCard.category_id == activity_category_id)

        rows = (await self._session.execute(query)).all()
        return [ActivityDistributionItem(date=day, count=int(count)) for day, count in rows]
