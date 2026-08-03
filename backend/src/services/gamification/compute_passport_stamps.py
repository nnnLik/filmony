from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from math import floor
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from const.passport_stamps import (
    COUNTRIES_IN_YEAR_TARGET,
    COUNTRIES_TOTAL_MILESTONES,
    PASSPORT_DECADES,
    PASSPORT_STAMP_BY_ID,
    country_slug,
)
from models.film import Film
from models.user_card import UserCard


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


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
        countries_by_year: dict[int, set[str]] = defaultdict(set)
        all_countries: set[str] = set()

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
            countries = [str(c).strip() for c in (row.countries or []) if str(c).strip()]
            cal_year = completed_at.astimezone(dt.UTC).year

            for country in countries:
                slug = country_slug(country)
                if slug not in country_first:
                    country_first[slug] = (completed_at, card_id, title, poster)
                countries_by_year[cal_year].add(country)
                all_countries.add(country)

            if year is not None:
                decade = floor(int(year) / 10) * 10
                if decade in PASSPORT_DECADES and decade not in decade_first:
                    decade_first[decade] = (completed_at, card_id, title, poster)

            if cal_year not in year_first:
                year_first[cal_year] = (completed_at, card_id, title, poster)

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

        unlocked_count = sum(1 for stamp in stamps if stamp.unlocked)
        return PassportStampsResult(stamps=stamps, unlocked_count=unlocked_count)
