from __future__ import annotations

import re
from collections import defaultdict
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
    return tuple(stamps)


PASSPORT_STAMP_CATALOG: tuple[PassportStampDefinition, ...] = build_passport_stamp_catalog()

PASSPORT_STAMP_BY_ID: dict[str, PassportStampDefinition] = {
    stamp.stamp_id: stamp for stamp in PASSPORT_STAMP_CATALOG
}

MARATHON_UNLOCK_COUNT = 5
