from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.franchises.franchise_label import resolve_franchise_label
from services.gamification.compute_marathon_achievements import ComputeMarathonAchievementsService
from services.gamification.compute_passport_stamps import ComputePassportStampsService

_RU_MONTHS = (
    '',
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь',
)


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


def _month_bounds(year: int, month: int) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime(year, month, 1, tzinfo=dt.UTC)
    if month == 12:
        end = dt.datetime(year + 1, 1, 1, tzinfo=dt.UTC)
    else:
        end = dt.datetime(year, month + 1, 1, tzinfo=dt.UTC)
    return start, end


def previous_complete_month(
    *,
    now: dt.datetime | None = None,
) -> tuple[int, int]:
    """Returns the calendar month immediately before ``now`` (UTC)."""
    if now is None:
        now = dt.datetime.now(tz=dt.UTC)
    first_of_current = dt.datetime(now.year, now.month, 1, tzinfo=dt.UTC)
    last_month_end = first_of_current - dt.timedelta(days=1)
    return last_month_end.year, last_month_end.month


@dataclass(frozen=True, slots=True)
class MonthlyRecapFilmItem:
    card_id: int
    film_id: int | None
    catalog_item_id: int | None
    title: str
    poster_url: str | None
    rating: float


@dataclass(frozen=True, slots=True)
class MonthlyRecapStampItem:
    stamp_id: str
    title: str
    unlocked_at: dt.datetime


@dataclass(frozen=True, slots=True)
class MonthlyRecapMarathonItem:
    kind: str
    key: str
    label: str
    unlocked_at: dt.datetime


@dataclass(frozen=True, slots=True)
class MonthlyRecapDistributionItem:
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class MonthlyRecapDecadeItem:
    decade_start: int
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class MonthlyRecapDirectorItem:
    kinopoisk_id: int
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class MonthlyRecapFranchiseItem:
    franchise_key: str
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class MonthlyRecap:
    user_id: UUID
    year: int
    month: int
    month_label: str
    total_rated: int
    average_rating: float
    top_films: list[MonthlyRecapFilmItem]
    new_stamps: list[MonthlyRecapStampItem]
    marathons_unlocked: list[MonthlyRecapMarathonItem]
    peak_activity_date: dt.date | None
    peak_activity_count: int
    genre_of_month: str | None
    genre_of_month_count: int
    top_director_name: str | None
    top_director_count: int
    top_director_kinopoisk_id: int | None
    top_country: str | None
    top_country_count: int
    new_countries_count: int
    genre_breakdown: list[MonthlyRecapDistributionItem]
    decade_breakdown: list[MonthlyRecapDecadeItem]
    director_breakdown: list[MonthlyRecapDirectorItem]
    franchise_breakdown: list[MonthlyRecapFranchiseItem]


@dataclass
class BuildMonthlyRecapService:
    """Aggregates a user's rated-card activity and gamification unlocks for one UTC calendar month."""

    _session: AsyncSession

    class InvalidMonth(Exception):
        pass

    class RecapNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, *, year: int, month: int) -> MonthlyRecap:
        if month < 1 or month > 12:
            raise self.InvalidMonth
        if year < 2000 or year > 2100:
            raise self.InvalidMonth

        month_start, month_end = _month_bounds(year, month)
        rows = (
            await self._session.execute(
                select(
                    UserCard.id,
                    UserCard.film_id,
                    UserCard.catalog_item_id,
                    UserCard.rating,
                    UserCard.display_title,
                    UserCard.display_cover_url,
                    _completion_timestamp().label('completed_at'),
                    Film.title,
                    Film.poster_url,
                    Film.genres,
                    Film.countries,
                    Film.year,
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                    Film.franchise_key,
                )
                .outerjoin(Film, Film.id == UserCard.film_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= month_start,
                    _completion_timestamp() < month_end,
                )
            )
        ).all()

        if not rows:
            raise self.RecapNotFound

        films: list[MonthlyRecapFilmItem] = []
        rating_sum = 0.0
        activity_by_day: Counter[dt.date] = Counter()
        genre_counter: Counter[str] = Counter()
        director_counter: dict[int, tuple[str, int]] = {}
        franchise_counter: Counter[str] = Counter()
        country_counter: Counter[str] = Counter()
        decade_counter: Counter[int] = Counter()
        month_countries: set[str] = set()

        for row in rows:
            rating_value = float(row.rating)
            rating_sum += rating_value
            completed_at = row.completed_at
            if completed_at is not None:
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=dt.UTC)
                activity_by_day[completed_at.date()] += 1

            title = row.title or row.display_title or 'Без названия'
            films.append(
                MonthlyRecapFilmItem(
                    card_id=int(row.id),
                    film_id=int(row.film_id) if row.film_id is not None else None,
                    catalog_item_id=int(row.catalog_item_id)
                    if row.catalog_item_id is not None
                    else None,
                    title=str(title),
                    poster_url=row.poster_url or row.display_cover_url,
                    rating=rating_value,
                )
            )

            if row.genres:
                for genre in row.genres:
                    if isinstance(genre, str) and genre.strip():
                        genre_counter[genre.strip()] += 1

            if row.primary_director_kinopoisk_id is not None:
                director_id = int(row.primary_director_kinopoisk_id)
                director_name = (
                    str(row.primary_director_name or '').strip() or f'Режиссёр #{director_id}'
                )
                existing_name, existing_count = director_counter.get(
                    director_id, (director_name, 0)
                )
                director_counter[director_id] = (
                    existing_name or director_name,
                    existing_count + 1,
                )

            if row.franchise_key:
                franchise_key = str(row.franchise_key).strip()
                if franchise_key:
                    franchise_counter[franchise_key] += 1

            if row.countries:
                for country in row.countries:
                    if isinstance(country, str) and country.strip():
                        label = country.strip()
                        country_counter[label] += 1
                        month_countries.add(label)

            if row.year is not None:
                decade_start = (int(row.year) // 10) * 10
                decade_counter[decade_start] += 1

        total_rated = len(films)
        average_rating = round(rating_sum / total_rated, 1) if total_rated else 0.0
        top_films = sorted(films, key=lambda item: (-item.rating, -item.card_id))[:3]

        peak_activity_date: dt.date | None = None
        peak_activity_count = 0
        if activity_by_day:
            peak_activity_date, peak_activity_count = activity_by_day.most_common(1)[0]

        genre_of_month: str | None = None
        genre_of_month_count = 0
        if genre_counter:
            genre_of_month, genre_of_month_count = genre_counter.most_common(1)[0]

        top_director_name: str | None = None
        top_director_count = 0
        top_director_kinopoisk_id: int | None = None
        if director_counter:
            top_director_kinopoisk_id, (top_director_name, top_director_count) = max(
                director_counter.items(),
                key=lambda item: (item[1][1], item[1][0]),
            )

        top_country: str | None = None
        top_country_count = 0
        if country_counter:
            top_country, top_country_count = country_counter.most_common(1)[0]

        new_countries_count = await self._count_new_countries_in_month(
            user_id=user_id,
            month_start=month_start,
            month_countries=month_countries,
        )

        genre_breakdown = [
            MonthlyRecapDistributionItem(label=genre, count=count)
            for genre, count in genre_counter.most_common(5)
        ]
        decade_breakdown = [
            MonthlyRecapDecadeItem(
                decade_start=decade_start,
                label=f'{decade_start}-е',
                count=count,
            )
            for decade_start, count in sorted(
                decade_counter.items(),
                key=lambda item: item[0],
            )
        ]
        director_breakdown = [
            MonthlyRecapDirectorItem(
                kinopoisk_id=kinopoisk_id,
                label=name,
                count=count,
            )
            for kinopoisk_id, (name, count) in sorted(
                director_counter.items(),
                key=lambda item: (-item[1][1], item[1][0]),
            )[:5]
        ]
        franchise_breakdown: list[MonthlyRecapFranchiseItem] = []
        for franchise_key, count in franchise_counter.most_common(5):
            franchise_breakdown.append(
                MonthlyRecapFranchiseItem(
                    franchise_key=franchise_key,
                    label=await resolve_franchise_label(self._session, franchise_key),
                    count=count,
                )
            )

        new_stamps = await self._stamps_unlocked_in_window(
            user_id=user_id,
            window_start=month_start,
            window_end=month_end,
        )
        marathons_unlocked = await self._marathons_unlocked_in_window(
            user_id=user_id,
            window_start=month_start,
            window_end=month_end,
        )

        month_label = f'{_RU_MONTHS[month].capitalize()} {year}'

        return MonthlyRecap(
            user_id=user_id,
            year=year,
            month=month,
            month_label=month_label,
            total_rated=total_rated,
            average_rating=average_rating,
            top_films=top_films,
            new_stamps=new_stamps,
            marathons_unlocked=marathons_unlocked,
            peak_activity_date=peak_activity_date,
            peak_activity_count=peak_activity_count,
            genre_of_month=genre_of_month,
            genre_of_month_count=genre_of_month_count,
            top_director_name=top_director_name,
            top_director_count=top_director_count,
            top_director_kinopoisk_id=top_director_kinopoisk_id,
            top_country=top_country,
            top_country_count=top_country_count,
            new_countries_count=new_countries_count,
            genre_breakdown=genre_breakdown,
            decade_breakdown=decade_breakdown,
            director_breakdown=director_breakdown,
            franchise_breakdown=franchise_breakdown,
        )

    async def _count_new_countries_in_month(
        self,
        *,
        user_id: UUID,
        month_start: dt.datetime,
        month_countries: set[str],
    ) -> int:
        if not month_countries:
            return 0

        prior_rows = (
            await self._session.execute(
                select(Film.countries)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() < month_start,
                )
            )
        ).all()

        prior_countries: set[str] = set()
        for (countries,) in prior_rows:
            if not countries:
                continue
            for country in countries:
                if isinstance(country, str) and country.strip():
                    prior_countries.add(country.strip())

        return len(month_countries - prior_countries)

    async def find_latest_recap_month(self, user_id: UUID) -> tuple[int, int] | None:
        row = (
            await self._session.execute(
                select(
                    func.extract('year', _completion_timestamp()).label('y'),
                    func.extract('month', _completion_timestamp()).label('m'),
                )
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                )
                .group_by('y', 'm')
                .order_by(
                    func.extract('year', _completion_timestamp()).desc(),
                    func.extract('month', _completion_timestamp()).desc(),
                )
                .limit(1)
            )
        ).first()
        if row is None:
            return None
        return int(row.y), int(row.m)

    async def _stamps_unlocked_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapStampItem]:
        result = await ComputePassportStampsService.build(self._session).execute(user_id)
        items: list[MonthlyRecapStampItem] = []
        for stamp in result.stamps:
            if not stamp.unlocked or stamp.unlocked_at is None:
                continue
            unlocked_at = stamp.unlocked_at
            if unlocked_at.tzinfo is None:
                unlocked_at = unlocked_at.replace(tzinfo=dt.UTC)
            if window_start <= unlocked_at < window_end:
                items.append(
                    MonthlyRecapStampItem(
                        stamp_id=stamp.stamp_id,
                        title=stamp.title,
                        unlocked_at=unlocked_at,
                    )
                )
        items.sort(key=lambda item: item.unlocked_at)
        return items

    async def _marathons_unlocked_in_window(
        self,
        *,
        user_id: UUID,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> list[MonthlyRecapMarathonItem]:
        achievements = await ComputeMarathonAchievementsService.build(self._session).execute(
            user_id
        )
        items: list[MonthlyRecapMarathonItem] = []
        for achievement in achievements:
            unlocked_at = achievement.unlocked_at
            if unlocked_at.tzinfo is None:
                unlocked_at = unlocked_at.replace(tzinfo=dt.UTC)
            if window_start <= unlocked_at < window_end:
                items.append(
                    MonthlyRecapMarathonItem(
                        kind=achievement.kind,
                        key=achievement.key,
                        label=achievement.label,
                        unlocked_at=unlocked_at,
                    )
                )
        items.sort(key=lambda item: item.unlocked_at)
        return items
