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
    total_films_in_db: int
    total_rated_films: int
    orphan_search_cache_films: int
    rated_without_director_name: int
    rated_without_franchise_key: int
    rated_without_countries: int
    rated_needs_enrichment: int
    rated_without_tmdb_sync: int
    rated_with_tmdb_id: int
    rated_without_director_kinopoisk_id: int
    # Legacy / all-film counters kept for tests and compare tooling
    without_director_kinopoisk_id: int
    without_director_name: int
    without_franchise_key: int
    without_countries: int
    needs_enrichment: int
    without_both_director_and_franchise: int
    only_director_missing: int
    only_franchise_missing: int
    without_tmdb_sync: int
    with_tmdb_id: int

    def pct_of_rated(self, part: int) -> float:
        if self.total_rated_films == 0:
            return 0.0
        return round(100.0 * part / self.total_rated_films, 1)

    def pct(self, part: int) -> float:
        if self.total_films_in_db == 0:
            return 0.0
        return round(100.0 * part / self.total_films_in_db, 1)


def _film_on_rated_card_expr() -> object:
    return _rated_film_exists_expr()


def _orphan_film_expr() -> object:
    return ~exists(
        select(UserCard.id).where(
            UserCard.film_id == Film.id,
        ),
    )


async def compute_film_tmdb_metadata_stats(session: AsyncSession) -> FilmTmdbMetadataStats:
    total = int((await session.execute(select(func.count()).select_from(Film))).scalar_one())

    total_rated = int(
        (
            await session.execute(
                select(func.count(func.distinct(Film.id)))
                .select_from(Film)
                .where(_film_on_rated_card_expr()),
            )
        ).scalar_one(),
    )
    orphan_search_cache = int(
        (
            await session.execute(
                select(func.count()).select_from(Film).where(_orphan_film_expr()),
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
    rated_without_countries = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    _countries_missing_expr(),
                ),
            )
        ).scalar_one(),
    )
    rated_needs_enrichment = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
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
    rated_without_tmdb_sync = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    Film.tmdb_synced_at.is_(None),
                ),
            )
        ).scalar_one(),
    )
    rated_with_tmdb_id = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    Film.tmdb_id.is_not(None),
                ),
            )
        ).scalar_one(),
    )
    rated_without_director_kp = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Film)
                .where(
                    _rated_film_exists_expr(),
                    Film.primary_director_kinopoisk_id.is_(None),
                ),
            )
        ).scalar_one(),
    )

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
        total_films_in_db=total,
        total_rated_films=total_rated,
        orphan_search_cache_films=orphan_search_cache,
        rated_without_director_name=rated_without_director,
        rated_without_franchise_key=rated_without_franchise,
        rated_without_countries=rated_without_countries,
        rated_needs_enrichment=rated_needs_enrichment,
        rated_without_tmdb_sync=rated_without_tmdb_sync,
        rated_with_tmdb_id=rated_with_tmdb_id,
        rated_without_director_kinopoisk_id=rated_without_director_kp,
        without_director_kinopoisk_id=without_director_kp,
        without_director_name=without_director_name,
        without_franchise_key=without_franchise,
        without_countries=without_countries,
        needs_enrichment=needs_enrichment,
        without_both_director_and_franchise=without_both,
        only_director_missing=only_director,
        only_franchise_missing=only_franchise,
        without_tmdb_sync=without_tmdb_sync,
        with_tmdb_id=with_tmdb_id,
    )


def format_film_tmdb_metadata_stats(stats: FilmTmdbMetadataStats) -> str:
    rp = stats.pct_of_rated
    lines = [
        '=== Film TMDB / gamification metadata (diagnostic) ===',
        '',
        '--- Scope (важно) ---',
        f'Оценённых фильмов (backfill scope): {stats.total_rated_films}',
        f'Всего строк film в БД:              {stats.total_films_in_db}',
        f'Кэш KP-поиска без карточек:         {stats.orphan_search_cache_films}',
        '',
        '--- Оценённые фильмы (prod metrics) ---',
        f'Нуждаются в enrichment:            {stats.rated_needs_enrichment} ({rp(stats.rated_needs_enrichment)}%)',
        f'Без director_name:                 {stats.rated_without_director_name} ({rp(stats.rated_without_director_name)}%)',
        f'Без franchise_key:                 {stats.rated_without_franchise_key} ({rp(stats.rated_without_franchise_key)}%)',
        f'Без countries:                     {stats.rated_without_countries} ({rp(stats.rated_without_countries)}%)',
        f'Без tmdb_synced_at:                {stats.rated_without_tmdb_sync} ({rp(stats.rated_without_tmdb_sync)}%)',
        f'С tmdb_id:                         {stats.rated_with_tmdb_id} ({rp(stats.rated_with_tmdb_id)}%)',
        f'Без director_kinopoisk_id:         {stats.rated_without_director_kinopoisk_id} ({rp(stats.rated_without_director_kinopoisk_id)}%)',
        '',
        '--- Вся таблица film (справочно, incl. search cache) ---',
        f'Нуждаются в enrichment:            {stats.needs_enrichment} ({stats.pct(stats.needs_enrichment)}%)',
        f'Без director_name:                 {stats.without_director_name} ({stats.pct(stats.without_director_name)}%)',
        f'Без franchise_key:                 {stats.without_franchise_key} ({stats.pct(stats.without_franchise_key)}%)',
        f'С tmdb_id:                         {stats.with_tmdb_id} ({stats.pct(stats.with_tmdb_id)}%)',
    ]
    return '\n'.join(lines)


__all__ = (
    'FilmTmdbMetadataStats',
    'compute_film_tmdb_metadata_stats',
    'format_film_tmdb_metadata_stats',
)
