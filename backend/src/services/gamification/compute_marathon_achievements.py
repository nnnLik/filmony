from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from const.passport_stamps import MARATHON_UNLOCK_COUNT
from models.film import Film
from models.user_card import UserCard


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


MarathonKind = Literal['director', 'franchise']


@dataclass(frozen=True, slots=True)
class MarathonAchievementDTO:
    kind: MarathonKind
    key: str
    label: str
    count: int
    unlocked_at: dt.datetime
    sample_poster_urls: list[str]


@dataclass
class ComputeMarathonAchievementsService:
    """Finds director and franchise rating marathons unlocked by a user."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[MarathonAchievementDTO]:
        rows = (
            await self._session.execute(
                select(
                    UserCard.id,
                    _completion_timestamp().label('completed_at'),
                    Film.poster_url,
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                    Film.franchise_key,
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

        director_groups: dict[int, list[tuple[dt.datetime, str | None]]] = {}
        franchise_groups: dict[str, list[tuple[dt.datetime, str | None]]] = {}

        for row in rows:
            completed_at = row.completed_at
            if completed_at is None:
                continue
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=dt.UTC)
            poster = row.poster_url
            director_id = row.primary_director_kinopoisk_id
            if director_id is not None:
                director_groups.setdefault(int(director_id), []).append((completed_at, poster))
            franchise_key = row.franchise_key
            if franchise_key:
                franchise_groups.setdefault(str(franchise_key), []).append((completed_at, poster))

        achievements: list[MarathonAchievementDTO] = []

        director_names: dict[int, str] = {}
        for row in rows:
            if row.primary_director_kinopoisk_id is not None and row.primary_director_name:
                director_names[int(row.primary_director_kinopoisk_id)] = str(
                    row.primary_director_name,
                )

        for director_id, entries in director_groups.items():
            if len(entries) < MARATHON_UNLOCK_COUNT:
                continue
            unlocked_at = entries[MARATHON_UNLOCK_COUNT - 1][0]
            posters = [poster for _, poster in entries if poster][:3]
            label = director_names.get(director_id, f'Режиссёр #{director_id}')
            achievements.append(
                MarathonAchievementDTO(
                    kind='director',
                    key=str(director_id),
                    label=label,
                    count=len(entries),
                    unlocked_at=unlocked_at,
                    sample_poster_urls=posters,
                ),
            )

        for franchise_key, entries in franchise_groups.items():
            if len(entries) < MARATHON_UNLOCK_COUNT:
                continue
            unlocked_at = entries[MARATHON_UNLOCK_COUNT - 1][0]
            posters = [poster for _, poster in entries if poster][:3]
            label = franchise_key.removeprefix('kp_franchise:')
            achievements.append(
                MarathonAchievementDTO(
                    kind='franchise',
                    key=franchise_key,
                    label=f'Франшиза {label}',
                    count=len(entries),
                    unlocked_at=unlocked_at,
                    sample_poster_urls=posters,
                ),
            )

        achievements.sort(key=lambda item: item.unlocked_at, reverse=True)
        return achievements
