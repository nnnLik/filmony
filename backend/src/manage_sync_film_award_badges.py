"""Sync Oscar Best Picture badges from curated Kinopoisk manifests.

Source manifests (git-tracked):
  ``src/data/curated/oscars/oscars_{2020..2026}_kinopoisk.json``

Production (from repo root):

  # dry-run
  DRY_RUN=1 make sync-film-award-badges

  # apply
  make sync-film-award-badges

Direct CLI (inside container, ``-w /opt/app``):

  python src/manage_sync_film_award_badges.py [--dry-run]

Idempotent: safe to re-run; upserts ``FilmAwardBadge`` rows only.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from core.database import get_session_factory
from services.film_award_badges.sync_film_award_badges import SyncFilmAwardBadgesService

_log = logging.getLogger(__name__)


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


async def _run(*, dry_run: bool) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await SyncFilmAwardBadgesService.build(session).execute(dry_run=dry_run)

    mode = 'dry-run' if dry_run else 'apply'
    _log.info(
        'sync film award badges (%s): files=%d rows=%d skipped_todo=%d matched=%d upserted=%d unmatched=%d',
        mode,
        result.files_processed,
        result.rows_seen,
        result.skipped_todo,
        result.matched,
        result.upserted,
        len(result.unmatched_kinopoisk_ids),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description='Sync Oscar Best Picture badges onto films.')
    parser.add_argument('--dry-run', action='store_true', help='Report counts without writing.')
    args = parser.parse_args()

    _configure_script_logging()
    asyncio.run(_run(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
