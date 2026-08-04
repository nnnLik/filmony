"""Backfill TMDB metadata for **rated** films only (countries, director, franchise).

Обрабатывает только ``Film``, у которых есть оценённая ``UserCard``
(``is_planned=false``, ``rating >= 1``). Кэш KP-поиска без карточек не трогаем.

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
    allow_kp_imdb_lookup: bool,
) -> None:
    _configure_script_logging()
    factory = get_session_factory()
    kp_transport = KinopoiskProviderTransport() if allow_kp_imdb_lookup else None
    syncer = SyncFilmFromTmdbService.build(kinopoisk_transport=kp_transport)
    processed = updated = skipped = errors = 0

    q = (
        select(Film.id)
        .where(_needs_tmdb_enrichment(force=force))
        .where(_rated_film_exists())
        .order_by(Film.id.asc())
    )
    if limit is not None:
        q = q.limit(limit)
    async with factory() as session:
        film_ids: list[int] = list((await session.execute(q)).scalars().all())
        total_rated = await _count_rated_films(session)

    total = len(film_ids)
    _log.info('=== TMDB backfill · только оценённые фильмы ===')
    _log.info('Оценённых фильмов в БД:     %s', total_rated)
    _log.info('К обработке (кандидаты):    %s', total)
    _log.info(
        'Режим: dry_run=%s | force=%s | kp_imdb_lookup=%s',
        dry_run,
        force,
        allow_kp_imdb_lookup,
    )
    if total == 0:
        _log.info('Нечего делать — все rated-кандидаты уже синхронизированы (или --limit 0).')
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
                    _log_progress_line(
                        index=processed,
                        total=total,
                        film=film,
                        status='DRY-RUN',
                        detail=(
                            f'imdb={film.imdb_id or "—"}, tmdb={film.tmdb_id or "—"}, '
                            f'director={film.primary_director_name or "—"}, '
                            f'franchise={film.franchise_key or "—"}'
                        ),
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
                        director = film.primary_director_name or '—'
                        franchise = film.franchise_key or '—'
                        _log_progress_line(
                            index=processed,
                            total=total,
                            film=film,
                            status='OK',
                            detail=(
                                f'tmdb_id={result.tmdb_id}, director={director}, franchise={franchise}'
                            ),
                        )
                    else:
                        skipped += 1
                        reason = result.reason or 'unknown'
                        _log_progress_line(
                            index=processed,
                            total=total,
                            film=film,
                            status='SKIP',
                            detail=reason,
                        )
        except Exception as exc:
            errors += 1
            _log.warning(
                '[%s/%s · осталось %s] film id=%s — ERROR: %s',
                processed,
                total,
                max(total - processed, 0),
                film_id,
                exc,
            )

        if processed % 25 == 0 or processed == total:
            _log.info(
                '--- checkpoint: %s/%s | ok=%s skip=%s err=%s | осталось %s ---',
                processed,
                total,
                updated,
                skipped,
                errors,
                max(total - processed, 0),
            )

        await asyncio.sleep(sleep_s)

    _log.info('=== Готово ===')
    _log.info('Обработано: %s/%s', processed, total)
    _log.info('Обновлено (TMDB sync): %s', updated)
    _log.info('Пропущено (TMDB not found / no match): %s', skipped)
    _log.info('Ошибок: %s', errors)
    _log.info('Dry-run: %s', dry_run)


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
    p.add_argument('--allow-kp-imdb-lookup', action='store_true')
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            force=args.force,
            force_gamification=args.force_overwrite_gamification,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            allow_kp_imdb_lookup=args.allow_kp_imdb_lookup,
        )
    )


if __name__ == '__main__':
    main()
