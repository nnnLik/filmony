"""Backfill Kinopoisk passport fields for rated films missing runtime or KP rating.

Обрабатывает только ``Film``, у которых есть оценённая ``UserCard``
(``is_planned=false``, ``rating >= 1``), и у которых ``film_length`` или
``rating_kinopoisk`` ещё не заполнены.

Запуск внутри backend (DATABASE_URL, KINOPOISK_* из env):

  alembic upgrade head
  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_kinopoisk_passport.py [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import exists, func, or_, select

from core.database import get_session_factory
from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError
from services.kinopoisk.resolve_kinopoisk_film import _apply_kinopoisk_passport

_log = logging.getLogger(__name__)

_QUIET_HTTP_LOGGERS = ('httpx', 'httpcore', 'hpack')


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    for name in _QUIET_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _film_label(film: Film) -> str:
    title = film.title.strip() or f'kp:{film.kinopoisk_id}'
    if len(title) > 48:
        title = f'{title[:45]}...'
    return title


def _needs_kinopoisk_passport(*, force: bool) -> object:
    if force:
        return True
    return or_(
        Film.film_length.is_(None),
        Film.rating_kinopoisk.is_(None),
    )


def _rated_film_exists() -> object:
    return exists(
        select(UserCard.id).where(
            UserCard.film_id == Film.id,
            *_rated_card_filters(),
        ),
    )


async def _count_rated_films(session) -> int:
    return int(
        (
            await session.execute(
                select(func.count(func.distinct(Film.id)))
                .select_from(Film)
                .where(_rated_film_exists()),
            )
        ).scalar_one(),
    )


async def _run(
    *,
    dry_run: bool,
    force: bool,
    sleep_s: float,
    limit: int | None,
) -> None:
    _configure_script_logging()
    factory = get_session_factory()
    client = KinopoiskClient()
    processed = updated = skipped = errors = 0

    q = (
        select(Film.id)
        .where(_needs_kinopoisk_passport(force=force))
        .where(_rated_film_exists())
        .order_by(Film.id.asc())
    )
    if limit is not None:
        q = q.limit(limit)

    async with factory() as session:
        film_ids: list[int] = list((await session.execute(q)).scalars().all())
        total_rated = await _count_rated_films(session)

    total = len(film_ids)
    _log.info('=== Kinopoisk passport backfill · только оценённые фильмы ===')
    _log.info('Оценённых фильмов в БД:     %s', total_rated)
    _log.info('К обработке (кандидаты):    %s', total)
    _log.info('Режим: dry_run=%s | force=%s', dry_run, force)
    if total == 0:
        _log.info('Нечего делать — все rated-кандидаты уже с passport-полями (или --limit 0).')
        return
    _log.info('---')

    for film_id in film_ids:
        processed += 1
        try:
            async with factory() as session:
                film = await session.get(Film, film_id)
                if film is None:
                    errors += 1
                    _log.warning(
                        '[%s/%s] film id=%s — ERROR: row missing',
                        processed,
                        total,
                        film_id,
                    )
                    continue
                if dry_run:
                    _log.info(
                        '[%s/%s] «%s» (kp=%s) — DRY-RUN: length=%s rating_kp=%s',
                        processed,
                        total,
                        _film_label(film),
                        film.kinopoisk_id,
                        film.film_length,
                        film.rating_kinopoisk,
                    )
                    continue
                payload = await client.get_film(film.kinopoisk_id)
                _apply_kinopoisk_passport(film, payload)
                await session.commit()
                updated += 1
                _log.info(
                    '[%s/%s] «%s» (kp=%s) — OK: length=%s rating_kp=%s rating_imdb=%s',
                    processed,
                    total,
                    _film_label(film),
                    film.kinopoisk_id,
                    film.film_length,
                    film.rating_kinopoisk,
                    film.rating_imdb,
                )
        except KinopoiskClientError as exc:
            skipped += 1
            _log.warning(
                '[%s/%s] film id=%s — SKIP: %s',
                processed,
                total,
                film_id,
                exc,
            )
        except Exception as exc:
            errors += 1
            _log.warning(
                '[%s/%s] film id=%s — ERROR: %s',
                processed,
                total,
                film_id,
                exc,
            )

        await asyncio.sleep(sleep_s)

    _log.info('=== Готово ===')
    _log.info('Обработано: %s/%s', processed, total)
    _log.info('Обновлено: %s', updated)
    _log.info('Пропущено (Kinopoisk error): %s', skipped)
    _log.info('Ошибок: %s', errors)
    _log.info('Dry-run: %s', dry_run)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument(
        '--force',
        action='store_true',
        help='include all rated films regardless of missing fields filter',
    )
    p.add_argument('--sleep', type=float, default=0.25)
    p.add_argument('--limit', type=int, default=None)
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
        ),
    )


if __name__ == '__main__':
    main()
