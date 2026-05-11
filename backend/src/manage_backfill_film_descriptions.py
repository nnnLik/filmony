"""Заполнить film.short_description и film.description из Kinopoisk API.

Запуск **внутри контейнера backend** (нужны DATABASE_URL, KINOPOISK_API_KEY,
KINOPOISK_API_BASE_URL из env_file):

  docker compose exec -w /opt/app backend python src/manage_backfill_film_descriptions.py

Опции::

  --dry-run          только лог, без commit
  --force            перезаписать даже если оба поля уже заполнены
  --sleep SEC        пауза между запросами к Kinopoisk (по умолчанию 0.06 ~16 rps)
  --limit N          обработать не больше N строк

Перед первым прогоном примените миграцию: ``make migrate``.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import select

from core.database import get_session_factory
from models.film import Film
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError

_log = logging.getLogger(__name__)


async def _run(*, dry_run: bool, force: bool, sleep_s: float, limit: int | None) -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    factory = get_session_factory()
    client = KinopoiskClient()
    processed = 0
    updated = 0
    errors = 0

    async with factory() as session:
        q = select(Film.id, Film.kinopoisk_id).order_by(Film.id.asc())
        if not force:
            q = q.where((Film.short_description.is_(None)) | (Film.description.is_(None)))
        if limit is not None:
            q = q.limit(limit)
        pairs: list[tuple[int, int]] = list((await session.execute(q)).all())

    for film_id, kinopoisk_id in pairs:
        processed += 1
        try:
            payload = await client.get_film(kinopoisk_id)
        except KinopoiskClientError as e:
            errors += 1
            _log.warning('kp film.id=%s kinopoisk_id=%s: %s', film_id, kinopoisk_id, e)
            await asyncio.sleep(sleep_s)
            continue

        if dry_run:
            short = payload.short_description or ''
            _log.info(
                'dry-run film id=%s kp=%s short=%r… desc_len=%s',
                film_id,
                kinopoisk_id,
                short[:80],
                len(payload.description or ''),
            )
        else:
            async with factory() as s2:
                row = await s2.get(Film, film_id)
                if row is None:
                    continue
                row.short_description = payload.short_description
                row.description = payload.description
                await s2.commit()
            updated += 1
            _log.info('updated film id=%s kinopoisk_id=%s', film_id, kinopoisk_id)

        await asyncio.sleep(sleep_s)

    _log.info(
        'done processed=%s updated=%s errors=%s dry_run=%s', processed, updated, errors, dry_run
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true', help='не писать в БД')
    p.add_argument('--force', action='store_true', help='перезаписать все')
    p.add_argument('--sleep', type=float, default=0.06, help='пауза между запросами к KP')
    p.add_argument('--limit', type=int, default=None, help='макс. число фильмов')
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
        )
    )


if __name__ == '__main__':
    main()
