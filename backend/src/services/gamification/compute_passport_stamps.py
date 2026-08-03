from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from math import floor
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from const.passport_stamps import (
    BINGE_DAY_TARGET,
    CHRONO_YEAR_TARGET,
    COUNTRIES_IN_YEAR_TARGET,
    COUNTRIES_TOTAL_MILESTONES,
    DIRECTOR_FAN_TARGET,
    GENRES_TOTAL_MILESTONES,
    HIGH_STREAK_TARGET,
    HORROR_SURVIVOR_TARGET,
    PASSPORT_DECADES,
    PASSPORT_STAMP_BY_ID,
    country_slug,
)
from models.film import Film
from models.user_card import UserCard


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


def _is_horror_genre(genre: str) -> bool:
    lowered = genre.strip().lower()
    return 'ужасы' in lowered or 'horror' in lowered


@dataclass(frozen=True, slots=True)
class PassportStampDTO:
    stamp_id: str
    title: str
    description: str
    unlocked: bool
    unlocked_at: dt.datetime | None
    progress_current: int | None
    progress_target: int | None
    unlock_card_id: int | None
    unlock_film_title: str | None
    unlock_film_poster_url: str | None


@dataclass(frozen=True, slots=True)
class PassportStampsResult:
    stamps: list[PassportStampDTO]
    unlocked_count: int


@dataclass
class ComputePassportStampsService:
    """Builds passport stamp progress from a user's rated film-backed cards."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> PassportStampsResult:
        rows = (
            await self._session.execute(
                select(
                    UserCard.id,
                    UserCard.rating,
                    _completion_timestamp().label('completed_at'),
                    Film.title,
                    Film.year,
                    Film.poster_url,
                    Film.countries,
                    Film.genres,
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                )
                .join(Film, Film.id == UserCard.film_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    UserCard.rating >= 1,
                )
                .order_by(_completion_timestamp().asc(), UserCard.id.asc()),
            )
        ).all()

        country_first: dict[str, tuple[dt.datetime, int, str, str | None]] = {}
        decade_first: dict[int, tuple[dt.datetime, int, str, str | None]] = {}
        year_first: dict[int, tuple[dt.datetime, int, str, str | None]] = {}
        director_first: dict[int, tuple[dt.datetime, int, str, str | None, str]] = {}
        countries_by_year: dict[int, set[str]] = defaultdict(set)
        decades_by_cal_year: dict[int, set[int]] = defaultdict(set)
        ratings_by_cal_day: dict[dt.date, int] = defaultdict(int)
        all_countries: set[str] = set()
        all_genres: set[str] = set()
        director_counts: dict[int, tuple[str, int]] = {}
        horror_count = 0
        first_rating_10: tuple[dt.datetime, int, str, str | None] | None = None
        first_rating_1: tuple[dt.datetime, int, str, str | None] | None = None
        high_streak = 0
        max_high_streak = 0
        high_streak_unlock: tuple[dt.datetime, int, str, str | None] | None = None
        completion_events: list[tuple[dt.datetime, float]] = []

        for row in rows:
            completed_at = row.completed_at
            if completed_at is None:
                continue
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=dt.UTC)
            card_id = int(row.id)
            title = str(row.title)
            poster = row.poster_url
            year = row.year
            rating = float(row.rating)
            countries = [str(c).strip() for c in (row.countries or []) if str(c).strip()]
            genres = [str(g).strip() for g in (row.genres or []) if str(g).strip()]
            cal_year = completed_at.astimezone(dt.UTC).year
            cal_day = completed_at.astimezone(dt.UTC).date()
            completion_events.append((completed_at, rating))

            for country in countries:
                slug = country_slug(country)
                if slug not in country_first:
                    country_first[slug] = (completed_at, card_id, title, poster)
                countries_by_year[cal_year].add(country)
                all_countries.add(country)

            for genre in genres:
                all_genres.add(genre.lower())
                if _is_horror_genre(genre):
                    horror_count += 1
                    break

            if year is not None:
                decade = floor(int(year) / 10) * 10
                if decade in PASSPORT_DECADES and decade not in decade_first:
                    decade_first[decade] = (completed_at, card_id, title, poster)
                decades_by_cal_year[cal_year].add(decade)

            if cal_year not in year_first:
                year_first[cal_year] = (completed_at, card_id, title, poster)

            ratings_by_cal_day[cal_day] += 1

            director_id = row.primary_director_kinopoisk_id
            director_name = str(row.primary_director_name or '')
            if director_id is not None:
                did = int(director_id)
                if did not in director_first:
                    director_first[did] = (completed_at, card_id, title, poster, director_name)
                prev = director_counts.get(did)
                director_counts[did] = (
                    director_name,
                    (prev[1] + 1) if prev else 1,
                )

            if rating >= 10 and first_rating_10 is None:
                first_rating_10 = (completed_at, card_id, title, poster)
            if rating <= 1 and first_rating_1 is None:
                first_rating_1 = (completed_at, card_id, title, poster)

            if rating >= 9:
                high_streak += 1
                max_high_streak = max(max_high_streak, high_streak)
                if high_streak >= HIGH_STREAK_TARGET and high_streak_unlock is None:
                    high_streak_unlock = (completed_at, card_id, title, poster)
            else:
                high_streak = 0

        mood_swings_unlocked = self._has_mood_swings_in_window(completion_events)

        stamps: list[PassportStampDTO] = []

        for slug, (unlocked_at, card_id, title, poster) in sorted(country_first.items()):
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'country_first_{slug}',
                    title=f'Первый раз: {slug.replace("_", " ").title()}',
                    description='Первая оценка фильма из этой страны',
                    unlocked=True,
                    unlocked_at=unlocked_at,
                    progress_current=None,
                    progress_target=None,
                    unlock_card_id=card_id,
                    unlock_film_title=title,
                    unlock_film_poster_url=poster,
                ),
            )

        for did, (unlocked_at, card_id, title, poster, director_name) in sorted(
            director_first.items(),
        ):
            label = director_name or f'Режиссёр {did}'
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'director_first_{did}',
                    title=f'Первый раз: {label}',
                    description='Первая оценка фильма этого режиссёра',
                    unlocked=True,
                    unlocked_at=unlocked_at,
                    progress_current=None,
                    progress_target=None,
                    unlock_card_id=card_id,
                    unlock_film_title=title,
                    unlock_film_poster_url=poster,
                ),
            )

        for decade in PASSPORT_DECADES:
            definition = PASSPORT_STAMP_BY_ID.get(f'decade_first_{decade}')
            title = definition.title if definition else f'Десятилетие {decade}-е'
            description = (
                definition.description if definition else f'Первая оценка фильма {decade}-х годов'
            )
            unlock = decade_first.get(decade)
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'decade_first_{decade}',
                    title=title,
                    description=description,
                    unlocked=unlock is not None,
                    unlocked_at=unlock[0] if unlock else None,
                    progress_current=None,
                    progress_target=None,
                    unlock_card_id=unlock[1] if unlock else None,
                    unlock_film_title=unlock[2] if unlock else None,
                    unlock_film_poster_url=unlock[3] if unlock else None,
                ),
            )

        for cal_year, unlock in sorted(year_first.items()):
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'year_first_rated_{cal_year}',
                    title=f'Первый просмотр {cal_year}',
                    description=f'Первая оценка в {cal_year} году',
                    unlocked=True,
                    unlocked_at=unlock[0],
                    progress_current=None,
                    progress_target=None,
                    unlock_card_id=unlock[1],
                    unlock_film_title=unlock[2],
                    unlock_film_poster_url=unlock[3],
                ),
            )

        for year in range(2020, 2031):
            current = len(countries_by_year.get(year, set()))
            definition = PASSPORT_STAMP_BY_ID.get(f'countries_5_in_{year}')
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'countries_5_in_{year}',
                    title=definition.title if definition else f'5 стран в {year}',
                    description=(
                        definition.description
                        if definition
                        else f'5 разных стран среди оценок за {year} год'
                    ),
                    unlocked=current >= COUNTRIES_IN_YEAR_TARGET,
                    unlocked_at=None,
                    progress_current=current,
                    progress_target=COUNTRIES_IN_YEAR_TARGET,
                    unlock_card_id=None,
                    unlock_film_title=None,
                    unlock_film_poster_url=None,
                ),
            )

        total_countries = len(all_countries)
        for milestone in COUNTRIES_TOTAL_MILESTONES:
            definition = PASSPORT_STAMP_BY_ID.get(f'countries_total_{milestone}')
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'countries_total_{milestone}',
                    title=definition.title if definition else f'{milestone} стран',
                    description=(
                        definition.description
                        if definition
                        else f'Оценил фильмы из {milestone} разных стран'
                    ),
                    unlocked=total_countries >= milestone,
                    unlocked_at=None,
                    progress_current=total_countries,
                    progress_target=milestone,
                    unlock_card_id=None,
                    unlock_film_title=None,
                    unlock_film_poster_url=None,
                ),
            )

        total_genres = len(all_genres)
        for milestone in GENRES_TOTAL_MILESTONES:
            definition = PASSPORT_STAMP_BY_ID.get(f'genres_total_{milestone}')
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'genres_total_{milestone}',
                    title=definition.title if definition else f'{milestone} жанров',
                    description=(
                        definition.description
                        if definition
                        else f'Оценил фильмы из {milestone} разных жанров'
                    ),
                    unlocked=total_genres >= milestone,
                    unlocked_at=None,
                    progress_current=total_genres,
                    progress_target=milestone,
                    unlock_card_id=None,
                    unlock_film_title=None,
                    unlock_film_poster_url=None,
                ),
            )

        for stamp_id, unlock in (
            ('first_rating_10', first_rating_10),
            ('first_rating_1', first_rating_1),
        ):
            definition = PASSPORT_STAMP_BY_ID.get(stamp_id)
            stamps.append(
                PassportStampDTO(
                    stamp_id=stamp_id,
                    title=definition.title if definition else stamp_id,
                    description=definition.description if definition else stamp_id,
                    unlocked=unlock is not None,
                    unlocked_at=unlock[0] if unlock else None,
                    progress_current=None,
                    progress_target=None,
                    unlock_card_id=unlock[1] if unlock else None,
                    unlock_film_title=unlock[2] if unlock else None,
                    unlock_film_poster_url=unlock[3] if unlock else None,
                ),
            )

        max_binge_day = max(ratings_by_cal_day.values()) if ratings_by_cal_day else 0
        binge_definition = PASSPORT_STAMP_BY_ID.get('binge_day')
        stamps.append(
            PassportStampDTO(
                stamp_id='binge_day',
                title=binge_definition.title if binge_definition else 'День марафона',
                description=(
                    binge_definition.description
                    if binge_definition
                    else '3 или больше оценок за один календарный день'
                ),
                unlocked=max_binge_day >= BINGE_DAY_TARGET,
                unlocked_at=None,
                progress_current=max_binge_day,
                progress_target=BINGE_DAY_TARGET,
                unlock_card_id=None,
                unlock_film_title=None,
                unlock_film_poster_url=None,
            ),
        )

        for year in range(2020, 2031):
            current = len(decades_by_cal_year.get(year, set()))
            definition = PASSPORT_STAMP_BY_ID.get(f'chrono_year_{year}')
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'chrono_year_{year}',
                    title=definition.title if definition else f'Хроно {year}',
                    description=(
                        definition.description
                        if definition
                        else f'3 разных десятилетия фильмов среди оценок за {year} год'
                    ),
                    unlocked=current >= CHRONO_YEAR_TARGET,
                    unlocked_at=None,
                    progress_current=current,
                    progress_target=CHRONO_YEAR_TARGET,
                    unlock_card_id=None,
                    unlock_film_title=None,
                    unlock_film_poster_url=None,
                ),
            )

        horror_definition = PASSPORT_STAMP_BY_ID.get('horror_survivor')
        stamps.append(
            PassportStampDTO(
                stamp_id='horror_survivor',
                title=horror_definition.title if horror_definition else 'Выживший в ужасах',
                description=(
                    horror_definition.description
                    if horror_definition
                    else '5 или больше фильмов жанра ужасы / horror'
                ),
                unlocked=horror_count >= HORROR_SURVIVOR_TARGET,
                unlocked_at=None,
                progress_current=horror_count,
                progress_target=HORROR_SURVIVOR_TARGET,
                unlock_card_id=None,
                unlock_film_title=None,
                unlock_film_poster_url=None,
            ),
        )

        streak_definition = PASSPORT_STAMP_BY_ID.get('high_streak_3')
        stamps.append(
            PassportStampDTO(
                stamp_id='high_streak_3',
                title=streak_definition.title if streak_definition else 'Серия девяток',
                description=(
                    streak_definition.description
                    if streak_definition
                    else '3 подряд оценки не ниже 9'
                ),
                unlocked=max_high_streak >= HIGH_STREAK_TARGET,
                unlocked_at=high_streak_unlock[0] if high_streak_unlock else None,
                progress_current=min(max_high_streak, HIGH_STREAK_TARGET),
                progress_target=HIGH_STREAK_TARGET,
                unlock_card_id=high_streak_unlock[1] if high_streak_unlock else None,
                unlock_film_title=high_streak_unlock[2] if high_streak_unlock else None,
                unlock_film_poster_url=high_streak_unlock[3] if high_streak_unlock else None,
            ),
        )

        mood_definition = PASSPORT_STAMP_BY_ID.get('mood_swings')
        stamps.append(
            PassportStampDTO(
                stamp_id='mood_swings',
                title=mood_definition.title if mood_definition else 'Качели настроения',
                description=(
                    mood_definition.description
                    if mood_definition
                    else 'За 7 дней есть и оценка ≤3, и оценка ≥9'
                ),
                unlocked=mood_swings_unlocked,
                unlocked_at=None,
                progress_current=None,
                progress_target=None,
                unlock_card_id=None,
                unlock_film_title=None,
                unlock_film_poster_url=None,
            ),
        )

        for did, (director_name, count) in sorted(director_counts.items()):
            label = director_name or f'Режиссёр {did}'
            stamps.append(
                PassportStampDTO(
                    stamp_id=f'director_fan_{did}',
                    title=f'Фанат: {label}',
                    description=f'3 фильма одного режиссёра ({label})',
                    unlocked=count >= DIRECTOR_FAN_TARGET,
                    unlocked_at=None,
                    progress_current=min(count, DIRECTOR_FAN_TARGET),
                    progress_target=DIRECTOR_FAN_TARGET,
                    unlock_card_id=None,
                    unlock_film_title=None,
                    unlock_film_poster_url=None,
                ),
            )

        unlocked_count = sum(1 for stamp in stamps if stamp.unlocked)
        return PassportStampsResult(stamps=stamps, unlocked_count=unlocked_count)

    @staticmethod
    def _has_mood_swings_in_window(
        events: list[tuple[dt.datetime, float]],
    ) -> bool:
        if len(events) < 2:
            return False
        sorted_events = sorted(events, key=lambda item: item[0])
        window = dt.timedelta(days=7)
        left = 0
        for right in range(len(sorted_events)):
            while sorted_events[right][0] - sorted_events[left][0] > window:
                left += 1
            window_ratings = [rating for _, rating in sorted_events[left : right + 1]]
            if any(rating <= 3 for rating in window_ratings) and any(
                rating >= 9 for rating in window_ratings
            ):
                return True
        return False
