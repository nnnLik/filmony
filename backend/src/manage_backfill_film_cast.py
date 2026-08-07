"""Backfill top-10 Kinopoisk ACTOR cast for films with rated user cards.

  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_cast.py [--dry-run] [--limit N]

Options: --dry-run, --limit N, --sleep SEC (default 0.15), --concurrency N (default 5)
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

_QUIET_HTTP_LOGGERS = ('httpx', 'httpcore', 'hpack')


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    for name in _QUIET_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


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
    concurrency: int,
) -> None:
    _configure_script_logging()
    factory = get_session_factory()
    progress_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(max(1, concurrency))
    processed = errors = 0

    async with factory() as session:
        film_ids: list[int] = list(
            (await session.execute(_films_without_cast_query(limit))).scalars().all()
        )

    total = len(film_ids)
    _log.info('=== Film cast backfill ===')
    _log.info('Candidates: %s', total)
    _log.info('Mode: dry_run=%s | concurrency=%s | sleep=%s', dry_run, concurrency, sleep_s)
    if total == 0:
        _log.info('Nothing to do.')
        return

    async def _process_film(film_id: int) -> None:
        nonlocal processed, errors
        async with semaphore:
            try:
                if dry_run:
                    async with progress_lock:
                        processed += 1
                        current = processed
                    _log.info('[%s/%s] film_id=%s — DRY-RUN', current, total, film_id)
                else:
                    async with factory() as session:
                        await EnsureFilmCastService.build(session).execute(film_id)
                    async with progress_lock:
                        processed += 1
                        current = processed
                    _log.info('[%s/%s] film_id=%s — OK', current, total, film_id)
            except Exception:
                async with progress_lock:
                    processed += 1
                    current = processed
                    errors += 1
                _log.exception('[%s/%s] film_id=%s — ERROR', current, total, film_id)

            if sleep_s > 0:
                await asyncio.sleep(sleep_s)

            async with progress_lock:
                checkpoint = processed
                err = errors
            if checkpoint % 25 == 0 or checkpoint == total:
                _log.info(
                    '--- checkpoint: %s/%s | errors=%s | remaining %s ---',
                    checkpoint,
                    total,
                    err,
                    max(total - checkpoint, 0),
                )

    await asyncio.gather(*[_process_film(film_id) for film_id in film_ids])

    _log.info('Done: processed=%s errors=%s', processed, errors)


def main() -> None:
    parser = argparse.ArgumentParser(description='Backfill Kinopoisk film cast for rated films')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--sleep', type=float, default=0.15)
    parser.add_argument('--concurrency', type=int, default=5)
    args = parser.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            concurrency=max(1, args.concurrency),
        ),
    )


if __name__ == '__main__':
    main()
