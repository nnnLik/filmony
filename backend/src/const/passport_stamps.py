from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


def country_slug(country: str) -> str:
    normalized = country.strip().lower()
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    return normalized.strip('_') or 'unknown'


PassportStampKind = Literal[
    'country_first',
    'decade_first',
    'countries_in_year',
    'countries_total',
    'year_first_rated',
    'director_first',
    'genres_total',
    'first_rating_extreme',
    'binge_day',
    'chrono_year',
    'horror_survivor',
    'high_streak',
    'mood_swings',
    'director_fan',
]


@dataclass(frozen=True, slots=True)
class PassportStampDefinition:
    stamp_id: str
    kind: PassportStampKind
    title: str
    description: str
    progress_target: int | None = None


PASSPORT_DECADES: tuple[int, ...] = tuple(range(1960, 2030, 10))
COUNTRIES_TOTAL_MILESTONES: tuple[int, ...] = (5, 10, 20)
COUNTRIES_IN_YEAR_TARGET = 5
GENRES_TOTAL_MILESTONES: tuple[int, ...] = (5, 10, 15)
BINGE_DAY_TARGET = 3
CHRONO_YEAR_TARGET = 3
HORROR_SURVIVOR_TARGET = 5
HIGH_STREAK_TARGET = 3
DIRECTOR_FAN_TARGET = 3


def build_passport_stamp_catalog() -> tuple[PassportStampDefinition, ...]:
    stamps: list[PassportStampDefinition] = []
    for decade in PASSPORT_DECADES:
        stamps.append(
            PassportStampDefinition(
                stamp_id=f'decade_first_{decade}',
                kind='decade_first',
                title=f'Десятилетие {decade}-е',
                description=f'Первая оценка фильма {decade}-х годов',
            ),
        )
    for milestone in COUNTRIES_TOTAL_MILESTONES:
        stamps.append(
            PassportStampDefinition(
                stamp_id=f'countries_total_{milestone}',
                kind='countries_total',
                title=f'{milestone} стран',
                description=f'Оценил фильмы из {milestone} разных стран',
                progress_target=milestone,
            ),
        )
    for year in range(2020, 2031):
        stamps.append(
            PassportStampDefinition(
                stamp_id=f'countries_5_in_{year}',
                kind='countries_in_year',
                title=f'5 стран в {year}',
                description=f'5 разных стран среди оценок за {year} год',
                progress_target=COUNTRIES_IN_YEAR_TARGET,
            ),
        )
    for milestone in GENRES_TOTAL_MILESTONES:
        stamps.append(
            PassportStampDefinition(
                stamp_id=f'genres_total_{milestone}',
                kind='genres_total',
                title=f'{milestone} жанров',
                description=f'Оценил фильмы из {milestone} разных жанров',
                progress_target=milestone,
            ),
        )
    stamps.append(
        PassportStampDefinition(
            stamp_id='first_rating_10',
            kind='first_rating_extreme',
            title='Первая десятка',
            description='Первый раз поставил оценку 10',
        ),
    )
    stamps.append(
        PassportStampDefinition(
            stamp_id='first_rating_1',
            kind='first_rating_extreme',
            title='Первая единица',
            description='Первый раз поставил оценку 1',
        ),
    )
    stamps.append(
        PassportStampDefinition(
            stamp_id='binge_day',
            kind='binge_day',
            title='День марафона',
            description='3 или больше оценок за один календарный день',
            progress_target=BINGE_DAY_TARGET,
        ),
    )
    for year in range(2020, 2031):
        stamps.append(
            PassportStampDefinition(
                stamp_id=f'chrono_year_{year}',
                kind='chrono_year',
                title=f'Хроно {year}',
                description=f'3 разных десятилетия фильмов среди оценок за {year} год',
                progress_target=CHRONO_YEAR_TARGET,
            ),
        )
    stamps.append(
        PassportStampDefinition(
            stamp_id='horror_survivor',
            kind='horror_survivor',
            title='Выживший в ужасах',
            description='5 или больше фильмов жанра ужасы / horror',
            progress_target=HORROR_SURVIVOR_TARGET,
        ),
    )
    stamps.append(
        PassportStampDefinition(
            stamp_id='high_streak_3',
            kind='high_streak',
            title='Серия девяток',
            description='3 подряд оценки не ниже 9',
            progress_target=HIGH_STREAK_TARGET,
        ),
    )
    stamps.append(
        PassportStampDefinition(
            stamp_id='mood_swings',
            kind='mood_swings',
            title='Качели настроения',
            description='За 7 дней есть и оценка ≤3, и оценка ≥9',
        ),
    )
    return tuple(stamps)


PASSPORT_STAMP_CATALOG: tuple[PassportStampDefinition, ...] = build_passport_stamp_catalog()

PASSPORT_STAMP_BY_ID: dict[str, PassportStampDefinition] = {
    stamp.stamp_id: stamp for stamp in PASSPORT_STAMP_CATALOG
}

MARATHON_UNLOCK_COUNT = 5
