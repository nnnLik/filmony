"""Aggregate TMDB / gamification metadata coverage stats for Film rows."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters


def _countries_missing_expr() -> object:
    return or_(
        Film.countries.is_(None),
        func.coalesce(func.json_array_length(Film.countries), 0) == 0,
    )


def _rated_film_exists_expr() -> object:
    return exists(
        select(UserCard.id).where(
            UserCard.film_id == Film.id,
            *_rated_card_filters(),
        ),
    )


@dataclass(frozen=True, slots=True)
class FilmTmdbMetadataStats:
    total_films: int
    without_director_kinopoisk_id: int
    without_director_name: int
    without_franchise_key: int
    without_countries: int
    needs_enrichment: int
    without_both_director_and_franchise: int
    only_director_missing: int
    only_franchise_missing: int
    rated_without_director_name: int
    rated_without_franchise_key: int
    without_tmdb_sync: int
    with_tmdb_id: int

    def pct(self, part: int) -> float:
        if self.total_films == 0:
            return 0.0
        return round(100.0 * part / self.total_films, 1)


async def compute_film_tmdb_metadata_stats(session: AsyncSession) -> FilmTmdbMetadataStats:
    total = int((await session.execute(select(func.count()).select_from(Film))).scalar_one())

    without_director_kp = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(Film.primary_director_kinopoisk_id.is_(None)),
            )
        ).scalar_one(),
    )
    without_director_name = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(Film.primary_director_name.is_(None)),
            )
        ).scalar_one(),
    )
    without_franchise = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(Film.franchise_key.is_(None)),
            )
        ).scalar_one(),
    )
    without_countries = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(_countries_missing_expr()),
            )
        ).scalar_one(),
    )
    needs_enrichment = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    or_(
                        _countries_missing_expr(),
                        Film.primary_director_name.is_(None),
                        Film.franchise_key.is_(None),
                        Film.tmdb_synced_at.is_(None),
                    ),
                ),
            )
        ).scalar_one(),
    )
    without_both = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    Film.primary_director_name.is_(None),
                    Film.franchise_key.is_(None),
                ),
            )
        ).scalar_one(),
    )
    only_director = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    Film.primary_director_name.is_(None),
                    Film.franchise_key.is_not(None),
                ),
            )
        ).scalar_one(),
    )
    only_franchise = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    Film.primary_director_name.is_not(None),
                    Film.franchise_key.is_(None),
                ),
            )
        ).scalar_one(),
    )
    rated_without_director = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    Film.primary_director_name.is_(None),
                ),
            )
        ).scalar_one(),
    )
    rated_without_franchise = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    Film.franchise_key.is_(None),
                ),
            )
        ).scalar_one(),
    )
    without_tmdb_sync = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(Film.tmdb_synced_at.is_(None)),
            )
        ).scalar_one(),
    )
    with_tmdb_id = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(Film.tmdb_id.is_not(None)),
            )
        ).scalar_one(),
    )

    return FilmTmdbMetadataStats(
        total_films=total,
        without_director_kinopoisk_id=without_director_kp,
        without_director_name=without_director_name,
        without_franchise_key=without_franchise,
        without_countries=without_countries,
        needs_enrichment=needs_enrichment,
        without_both_director_and_franchise=without_both,
        only_director_missing=only_director,
        only_franchise_missing=only_franchise,
        rated_without_director_name=rated_without_director,
        rated_without_franchise_key=rated_without_franchise,
        without_tmdb_sync=without_tmdb_sync,
        with_tmdb_id=with_tmdb_id,
    )


def format_film_tmdb_metadata_stats(stats: FilmTmdbMetadataStats) -> str:
    p = stats.pct
    lines = [
        '=== Film TMDB / gamification metadata (diagnostic) ===',
        f'Всего фильмов в БД:              {stats.total_films}',
        '',
        '--- Режиссёр ---',
        f'Без director_kinopoisk_id:         {stats.without_director_kinopoisk_id} ({p(stats.without_director_kinopoisk_id)}%)',
        f'Без director_name:               {stats.without_director_name} ({p(stats.without_director_name)}%)',
        '',
        '--- Франшиза / серия ---',
        f'Без franchise_key:               {stats.without_franchise_key} ({p(stats.without_franchise_key)}%)',
        '',
        '--- TMDB sync ---',
        f'Без tmdb_synced_at:              {stats.without_tmdb_sync} ({p(stats.without_tmdb_sync)}%)',
        f'С tmdb_id:                       {stats.with_tmdb_id} ({p(stats.with_tmdb_id)}%)',
        '',
        '--- Прочее gamification metadata ---',
        f'Без countries:                   {stats.without_countries} ({p(stats.without_countries)}%)',
        f'Нуждаются в enrichment (любое):  {stats.needs_enrichment} ({p(stats.needs_enrichment)}%)',
        '',
        '--- Пересечения ---',
        f'Нет и режиссёра, и franchise:    {stats.without_both_director_and_franchise}',
        f'Только режиссёр отсутствует:     {stats.only_director_missing}',
        f'Только franchise отсутствует:    {stats.only_franchise_missing}',
        '',
        '--- Влияние на оценённые карточки ---',
        f'Оценённых фильмов без режиссёра: {stats.rated_without_director_name}',
        f'Оценённых фильмов без franchise: {stats.rated_without_franchise_key}',
    ]
    return '\n'.join(lines)


__all__ = (
    'FilmTmdbMetadataStats',
    'compute_film_tmdb_metadata_stats',
    'format_film_tmdb_metadata_stats',
)
