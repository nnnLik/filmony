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
        )

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
