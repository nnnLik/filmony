"""Догон metadata для gamification: countries, director, franchise_key.

Запуск внутри backend (DATABASE_URL, KINOPOISK_* из env):

  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_gamification_metadata.py [--dry-run] [--limit N]

Опции: --dry-run, --force, --sleep SEC (default 0.15), --limit N,
       --skip-staff, --skip-sequels (только countries из get_film)
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import func, or_, select

from core.database import get_session_factory
from models.film import Film
from services.gamification.enrich_film_gamification_metadata import (
    EnrichFilmGamificationMetadataService,
)

_log = logging.getLogger(__name__)


def _needs_enrichment(force: bool) -> object:
    if force:
        return True
    countries_missing = or_(
        Film.countries.is_(None),
        func.coalesce(func.json_array_length(Film.countries), 0) == 0,
    )
    return or_(
        countries_missing,
        Film.primary_director_kinopoisk_id.is_(None),
        Film.franchise_key.is_(None),
    )


async def _run(
    *,
    dry_run: bool,
    force: bool,
    sleep_s: float,
    limit: int | None,
    skip_staff: bool,
    skip_sequels: bool,
) -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    factory = get_session_factory()
    enricher = EnrichFilmGamificationMetadataService.build()
    processed = updated = errors = 0

    async with factory() as session:
        q = (
            select(Film.id, Film.kinopoisk_id)
            .where(_needs_enrichment(force))
            .order_by(Film.id.asc())
        )
        if limit is not None:
            q = q.limit(limit)
        rows: list[tuple[int, int]] = list((await session.execute(q)).all())

    for film_id, kinopoisk_id in rows:
        processed += 1
        try:
            if dry_run:
                preview = await enricher.preview(
                    kinopoisk_id=kinopoisk_id,
                    skip_staff=skip_staff,
                    skip_sequels=skip_sequels,
                )
                _log.info(
                    'dry-run film id=%s kp=%s countries=%s director=%s franchise=%s',
                    film_id,
                    kinopoisk_id,
                    preview.countries,
                    preview.primary_director_name,
                    preview.franchise_key,
                )
            else:
                async with factory() as session:
                    film = await session.get(Film, film_id)
                    if film is None:
                        continue
                    await enricher.execute(
                        session=session,
                        film=film,
                        skip_staff=skip_staff,
                        skip_sequels=skip_sequels,
                    )
                    await session.commit()
                updated += 1
                _log.info('updated film id=%s kinopoisk_id=%s', film_id, kinopoisk_id)
        except Exception as exc:
            errors += 1
            _log.warning('film id=%s kp=%s failed: %s', film_id, kinopoisk_id, exc)

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
    p.add_argument('--force', action='store_true', help='перезаписать все Film')
    p.add_argument('--sleep', type=float, default=0.15)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--skip-staff', action='store_true')
    p.add_argument('--skip-sequels', action='store_true')
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            skip_staff=args.skip_staff,
            skip_sequels=args.skip_sequels,
        )
    )


if __name__ == '__main__':
    main()
