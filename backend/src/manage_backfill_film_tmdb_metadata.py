"""Backfill Film metadata from TMDB (countries, director name, franchise).

Запуск внутри backend (DATABASE_URL, TMDB_* из env):

  alembic upgrade head
  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_tmdb_metadata.py [--dry-run] [--limit N]

Покрытие: ``src/tests/scripts/test_manage_backfill_film_tmdb_metadata.py``
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import exists, func, or_, select

from core.database import get_session_factory
from models.film import Film
from models.user_card import UserCard
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from services.directors.get_director_summary import _rated_card_filters
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService

_log = logging.getLogger(__name__)


def _countries_missing() -> object:
    return or_(
        Film.countries.is_(None),
        func.coalesce(func.json_array_length(Film.countries), 0) == 0,
    )


def _needs_tmdb_enrichment(*, force: bool) -> object:
    if force:
        return True
    return or_(
        _countries_missing(),
        Film.primary_director_name.is_(None),
        Film.franchise_key.is_(None),
        Film.tmdb_synced_at.is_(None),
    )


def _rated_film_exists() -> object:
    return exists(
        select(UserCard.id).where(
            UserCard.film_id == Film.id,
            *_rated_card_filters(),
        ),
    )


async def _run(
    *,
    dry_run: bool,
    force: bool,
    force_gamification: bool,
    sleep_s: float,
    limit: int | None,
    rated_only: bool,
    allow_kp_imdb_lookup: bool,
) -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    factory = get_session_factory()
    kp_transport = KinopoiskProviderTransport() if allow_kp_imdb_lookup else None
    syncer = SyncFilmFromTmdbService.build(kinopoisk_transport=kp_transport)
    processed = updated = errors = 0

    q = select(Film.id).where(_needs_tmdb_enrichment(force=force)).order_by(Film.id.asc())
    if rated_only:
        q = q.where(_rated_film_exists())
    if limit is not None:
        q = q.limit(limit)
    async with factory() as session:
        film_ids: list[int] = list((await session.execute(q)).scalars().all())

    for film_id in film_ids:
        processed += 1
        try:
            async with factory() as session:
                film = await session.get(Film, film_id)
                if film is None:
                    continue
                if dry_run:
                    _log.info(
                        'dry-run film id=%s kp=%s imdb=%s tmdb=%s director=%s franchise=%s',
                        film_id,
                        film.kinopoisk_id,
                        film.imdb_id,
                        film.tmdb_id,
                        film.primary_director_name,
                        film.franchise_key,
                    )
                else:
                    result = await syncer.execute(
                        session,
                        film,
                        force_gamification=force_gamification,
                        allow_kp_imdb_lookup=allow_kp_imdb_lookup,
                    )
                    await session.commit()
                    if result.synced:
                        updated += 1
                        _log.info(
                            'updated film id=%s tmdb_id=%s imdb=%s',
                            film_id,
                            result.tmdb_id,
                            result.imdb_id,
                        )
                    else:
                        _log.warning(
                            'film id=%s not synced: %s',
                            film_id,
                            result.reason,
                        )
        except Exception as exc:
            errors += 1
            _log.warning('film id=%s failed: %s', film_id, exc)

        await asyncio.sleep(sleep_s)

    _log.info(
        'done processed=%s updated=%s errors=%s dry_run=%s',
        processed,
        updated,
        errors,
        dry_run,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument(
        '--force',
        action='store_true',
        help='include all films regardless of missing fields filter',
    )
    p.add_argument(
        '--force-overwrite-gamification',
        action='store_true',
        help='overwrite gamification fields except existing kp_franchise keys',
    )
    p.add_argument('--sleep', type=float, default=0.25)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--rated-only', action=argparse.BooleanOptionalAction, default=True)
    p.add_argument('--allow-kp-imdb-lookup', action='store_true')
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            force_gamification=args.force_overwrite_gamification,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            rated_only=args.rated_only,
            allow_kp_imdb_lookup=args.allow_kp_imdb_lookup,
        )
    )


if __name__ == '__main__':
    main()
