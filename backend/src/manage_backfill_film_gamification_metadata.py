"""Догон metadata для gamification: countries, director, franchise_key.

Обрабатывает только ``Film``, у которых есть хотя бы одна ``UserCard``
(``user_card.film_id IS NOT NULL``). Кэш KP-поиска без карточек не трогаем.

Запуск внутри backend (DATABASE_URL, KINOPOISK_* из env):

  alembic upgrade head   # обязательно до первого прогона
  docker compose exec -w /opt/app backend \\
    python src/manage_backfill_film_gamification_metadata.py [--dry-run] [--limit N]

Покрытие: ``src/tests/scripts/test_manage_backfill_film_gamification_metadata.py``

Опции: --dry-run, --force, --sleep SEC (default 0.15), --limit N,
       --skip-staff, --skip-sequels (только countries из get_film),
       --rated-only (только оценённые карточки), --concurrency N (default 5)
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
from services.gamification.enrich_film_gamification_metadata import (
    EnrichFilmGamificationMetadataService,
)

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


def _log_progress_line(
    *,
    index: int,
    total: int,
    film: Film,
    status: str,
    detail: str,
) -> None:
    remaining = max(total - index, 0)
    pct = round(100.0 * index / total, 1) if total else 100.0
    _log.info(
        '[%s/%s · %.1f%% · осталось %s] «%s» (kp=%s) — %s%s',
        index,
        total,
        pct,
        remaining,
        _film_label(film),
        film.kinopoisk_id,
        status,
        f': {detail}' if detail else '',
    )


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


def _film_on_user_card_exists(*, rated_only: bool = False) -> object:
    filters = (
        (
            UserCard.film_id == Film.id,
            *_rated_card_filters(),
        )
        if rated_only
        else (UserCard.film_id == Film.id,)
    )
    return exists(select(UserCard.id).where(*filters))


async def _count_films_on_cards(session, *, rated_only: bool) -> int:
    return int(
        (
            await session.execute(
                select(func.count(func.distinct(Film.id)))
                .select_from(Film)
                .where(_film_on_user_card_exists(rated_only=rated_only)),
            )
        ).scalar_one(),
    )


async def _run(
    *,
    dry_run: bool,
    force: bool,
    rated_only: bool,
    sleep_s: float,
    limit: int | None,
    skip_staff: bool,
    skip_sequels: bool,
    concurrency: int,
) -> None:
    _configure_script_logging()
    factory = get_session_factory()
    enricher = EnrichFilmGamificationMetadataService.build()
    processed = updated = errors = 0
    progress_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(max(1, concurrency))

    q = (
        select(Film.id)
        .where(_needs_enrichment(force))
        .where(_film_on_user_card_exists(rated_only=rated_only))
        .order_by(Film.id.asc())
    )
    if limit is not None:
        q = q.limit(limit)
    async with factory() as session:
        film_ids: list[int] = list((await session.execute(q)).scalars().all())
        total_on_cards = await _count_films_on_cards(session, rated_only=rated_only)

    total = len(film_ids)
    scope = 'оценённые' if rated_only else 'с карточками'
    _log.info('=== Gamification backfill · только фильмы %s ===', scope)
    _log.info('Фильмов %s в БД:           %s', scope, total_on_cards)
    _log.info('К обработке (кандидаты):    %s', total)
    _log.info(
        'Режим: dry_run=%s | force=%s | rated_only=%s | concurrency=%s',
        dry_run,
        force,
        rated_only,
        concurrency,
    )
    if total == 0:
        _log.info('Нечего делать — все кандидаты уже обогащены (или --limit 0).')
        return
    _log.info('---')

    async def _process_film(film_id: int) -> None:
        nonlocal processed, updated, errors
        async with semaphore:
            try:
                async with factory() as session:
                    film = await session.get(Film, film_id)
                    if film is None:
                        async with progress_lock:
                            processed += 1
                            current = processed
                            errors += 1
                        _log.warning(
                            '[%s/%s] film id=%s — ERROR: row missing',
                            current,
                            total,
                            film_id,
                        )
                        return
                    if dry_run:
                        preview = await enricher.preview(
                            kinopoisk_id=film.kinopoisk_id,
                            skip_staff=skip_staff,
                            skip_sequels=skip_sequels,
                        )
                        async with progress_lock:
                            processed += 1
                            current = processed
                        _log_progress_line(
                            index=current,
                            total=total,
                            film=film,
                            status='DRY-RUN',
                            detail=(
                                f'countries={preview.countries!r}, '
                                f'director={preview.primary_director_name or "—"}, '
                                f'franchise={preview.franchise_key or "—"}'
                            ),
                        )
                    else:
                        await enricher.execute(
                            session=session,
                            film=film,
                            skip_staff=skip_staff,
                            skip_sequels=skip_sequels,
                        )
                        await session.commit()
                        async with progress_lock:
                            processed += 1
                            current = processed
                            updated += 1
                        _log_progress_line(
                            index=current,
                            total=total,
                            film=film,
                            status='OK',
                            detail=(
                                f'director={film.primary_director_name or "—"}, '
                                f'franchise={film.franchise_key or "—"}'
                            ),
                        )
            except Exception as exc:
                async with progress_lock:
                    processed += 1
                    current = processed
                    errors += 1
                _log.warning(
                    '[%s/%s · осталось %s] film id=%s — ERROR: %s',
                    current,
                    total,
                    max(total - current, 0),
                    film_id,
                    exc,
                )

            async with progress_lock:
                checkpoint = processed
                ok = updated
                err = errors
            if checkpoint % 25 == 0 or checkpoint == total:
                _log.info(
                    '--- checkpoint: %s/%s | ok=%s err=%s | осталось %s ---',
                    checkpoint,
                    total,
                    ok,
                    err,
                    max(total - checkpoint, 0),
                )

            await asyncio.sleep(sleep_s)

    await asyncio.gather(*[_process_film(fid) for fid in film_ids])

    _log.info('=== Готово ===')
    _log.info('Обработано: %s/%s', processed, total)
    _log.info('Обновлено: %s', updated)
    _log.info('Ошибок: %s', errors)
    _log.info('Dry-run: %s', dry_run)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--force', action='store_true', help='перезаписать все Film с карточками')
    p.add_argument(
        '--rated-only',
        action='store_true',
        help='только фильмы с оценёнными карточками (is_planned=false, rating>=1)',
    )
    p.add_argument('--sleep', type=float, default=0.15)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--skip-staff', action='store_true')
    p.add_argument('--skip-sequels', action='store_true')
    p.add_argument('--concurrency', type=int, default=5)
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            rated_only=args.rated_only,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            skip_staff=args.skip_staff,
            skip_sequels=args.skip_sequels,
            concurrency=max(1, args.concurrency),
        )
    )


if __name__ == '__main__':
    main()
