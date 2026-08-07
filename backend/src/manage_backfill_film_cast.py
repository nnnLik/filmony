"""Backfill top-10 Kinopoisk ACTOR cast for films with rated user cards.

  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_cast.py [--dry-run] [--limit N]

Options: --dry-run, --limit N, --sleep SEC (default 0.15), --batch-size (default 50)
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import exists, select

from core.database import get_session_factory
from models.film import Film
from models.film_actor import FilmActor
from models.user_card import UserCard
from services.cast.ensure_film_cast import EnsureFilmCastService
from services.directors.get_director_summary import _rated_card_filters

_log = logging.getLogger(__name__)


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


def _films_without_cast_query(limit: int | None):
    q = (
        select(Film.id)
        .where(
            exists(
                select(UserCard.id).where(
                    UserCard.film_id == Film.id,
                    *_rated_card_filters(),
                ),
            ),
        )
        .where(
            ~exists(
                select(FilmActor.id).where(FilmActor.film_id == Film.id),
            ),
        )
        .order_by(Film.id.asc())
    )
    if limit is not None:
        q = q.limit(limit)
    return q


async def _run(
    *,
    dry_run: bool,
    sleep_s: float,
    limit: int | None,
    batch_size: int,
) -> None:
    _configure_script_logging()
    factory = get_session_factory()
    async with factory() as session:
        film_ids: list[int] = list(
            (await session.execute(_films_without_cast_query(limit))).scalars().all()
        )

    total = len(film_ids)
    _log.info('=== Film cast backfill ===')
    _log.info('Candidates: %s', total)
    if total == 0:
        _log.info('Nothing to do.')
        return

    processed = errors = 0
    for start in range(0, total, batch_size):
        batch = film_ids[start : start + batch_size]
        for film_id in batch:
            if dry_run:
                processed += 1
                _log.info('[%s/%s] film_id=%s — DRY-RUN', processed, total, film_id)
                continue
            try:
                async with factory() as session:
                    await EnsureFilmCastService.build(session).execute(film_id)
                processed += 1
                _log.info('[%s/%s] film_id=%s — OK', processed, total, film_id)
            except Exception:
                errors += 1
                processed += 1
                _log.exception('[%s/%s] film_id=%s — ERROR', processed, total, film_id)
            if sleep_s > 0:
                await asyncio.sleep(sleep_s)

    _log.info('Done: processed=%s errors=%s', processed, errors)


def main() -> None:
    parser = argparse.ArgumentParser(description='Backfill Kinopoisk film cast for rated films')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--sleep', type=float, default=0.15)
    parser.add_argument('--batch-size', type=int, default=50)
    args = parser.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            sleep_s=args.sleep,
            limit=args.limit,
            batch_size=max(1, args.batch_size),
        ),
    )


if __name__ == '__main__':
    main()
