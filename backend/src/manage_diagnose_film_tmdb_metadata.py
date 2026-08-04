"""Print TMDB / gamification metadata coverage stats for Film rows.

Запуск внутри backend:

  docker compose exec -w /opt/app backend \\
    python src/manage_diagnose_film_tmdb_metadata.py

После backfill:

  python src/manage_backfill_film_tmdb_metadata.py --limit 10
  python src/manage_diagnose_film_tmdb_metadata.py
"""

from __future__ import annotations

import asyncio

from core.database import get_session_factory
from services.tmdb.film_tmdb_metadata_stats import (
    compute_film_tmdb_metadata_stats,
    format_film_tmdb_metadata_stats,
)


async def _run() -> None:
    factory = get_session_factory()
    async with factory() as session:
        stats = await compute_film_tmdb_metadata_stats(session)
    print(format_film_tmdb_metadata_stats(stats))


def main() -> None:
    asyncio.run(_run())


if __name__ == '__main__':
    main()
