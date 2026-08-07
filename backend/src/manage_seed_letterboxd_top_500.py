"""Seed the evergreen ``letterboxd-top-500`` collection from curated Kinopoisk mapping.

Source manifest (git-tracked):
  ``src/data/curated/letterboxd_top_500_kinopoisk.json``

Original mapping pipeline (not run in prod):
  ``.cursor/active/collections-core/data/map_lb_kp.py`` +
  ``.cursor/active/collections-core/data/letterboxd_top_500_kinopoisk.json``

Production (from repo root; backend container must be running with ``DATABASE_URL`` +
Kinopoisk credentials). Full runbook: ``.cursor/active/collections-core/PROD_SEED.md``.

  # 1) migrate once
  docker compose exec -w /opt/app filmony-backend alembic upgrade head

  # 2) dry-run (recommended first)
  DRY_RUN=1 make seed-letterboxd-top-500

  # 3) apply seed (~500 films)
  make seed-letterboxd-top-500

  # optional: LIMIT=10 SLEEP=0.5 DRY_RUN=1 make seed-letterboxd-top-500

Direct CLI (inside container, ``-w /opt/app``):

  python src/manage_seed_letterboxd_top_500.py [--dry-run] [--limit N] [--sleep 0.2]

Idempotent: safe to re-run; upserts ``Collection`` / ``CollectionFilm`` only (no user progress).
Bulk seed skips TMDB enrich to avoid ``ix_film_tmdb_id`` collisions; use backfill if needed.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from core.database import get_session_factory
from models.collection import Collection, CollectionKind
from models.collection_film import CollectionFilm
from models.film import Film
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError

_log = logging.getLogger(__name__)

_COLLECTION_SLUG = 'letterboxd-top-500'
_COLLECTION_TITLE = 'Letterboxd Top 500'
_COLLECTION_DESCRIPTION = (
    'Пятьсот лучших фильмов по версии Letterboxd — классика, культ и вечные споры. '
    'Отмечайте, сколько уже в копилке.'
)
_MANIFEST_PATH = Path(__file__).resolve().parent / 'data/curated/letterboxd_top_500_kinopoisk.json'

_QUIET_HTTP_LOGGERS = ('httpx', 'httpcore', 'hpack')


@dataclass(frozen=True, slots=True)
class SeedRow:
    rank: int
    letterboxd_name: str
    year: int | None
    kinopoisk_id: int
    imdb_id: str | None


@dataclass
class SeedSummary:
    created_films: int = 0
    reused_films: int = 0
    linked: int = 0
    updated_links: int = 0
    skipped_todo: int = 0
    errors: int = 0


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    for name in _QUIET_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _kinopoisk_film_url(kinopoisk_id: int) -> str:
    return f'https://www.kinopoisk.ru/film/{kinopoisk_id}/'


def _load_manifest(path: Path) -> tuple[list[SeedRow], int]:
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
    skipped_todo = sum(1 for item in raw if item.get('kinopoisk_id') == 'TODO')
    rows: list[SeedRow] = []
    for item in raw:
        kp = item.get('kinopoisk_id')
        if kp == 'TODO' or kp is None:
            continue
        if not isinstance(kp, int):
            raise TypeError(f'invalid kinopoisk_id for rank {item.get("rank")}: {kp!r}')
        imdb = item.get('imdb_id')
        rows.append(
            SeedRow(
                rank=int(item['rank']),
                letterboxd_name=str(item.get('letterboxd_name') or ''),
                year=int(item['year']) if item.get('year') is not None else None,
                kinopoisk_id=kp,
                imdb_id=str(imdb) if imdb else None,
            ),
        )
    rows.sort(key=lambda r: r.rank)
    return rows, skipped_todo


async def _get_or_create_collection(
    session,
    *,
    content_updated_at: dt.datetime,
) -> Collection:
    existing = (
        await session.execute(select(Collection).where(Collection.slug == _COLLECTION_SLUG))
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = _COLLECTION_TITLE
        existing.description = _COLLECTION_DESCRIPTION
        existing.kind = CollectionKind.evergreen
        existing.is_active = True
        existing.content_updated_at = content_updated_at
        return existing

    collection = Collection(
        slug=_COLLECTION_SLUG,
        kind=CollectionKind.evergreen,
        title=_COLLECTION_TITLE,
        description=_COLLECTION_DESCRIPTION,
        season_year=None,
        is_active=True,
        film_count=0,
        content_updated_at=content_updated_at,
    )
    session.add(collection)
    await session.flush()
    return collection


async def _create_film_from_kinopoisk(
    session,
    *,
    row: SeedRow,
    client: KinopoiskClient,
) -> Film:
    payload = await client.get_film(row.kinopoisk_id)
    imdb_id = payload.imdb_id or row.imdb_id
    film = Film(
        kinopoisk_id=payload.kinopoisk_id,
        title=payload.title,
        year=payload.year,
        poster_url=payload.poster_url,
        genres=payload.genres,
        countries=payload.countries,
        short_description=payload.short_description,
        description=payload.description,
        imdb_id=imdb_id,
    )
    session.add(film)
    await session.flush()
    return film


async def _ensure_film(
    session,
    *,
    row: SeedRow,
    kp_client: KinopoiskClient,
    dry_run: bool,
) -> tuple[Film | None, bool]:
    """Return (film, created_via_kp_api)."""
    existing = (
        await session.execute(select(Film).where(Film.kinopoisk_id == row.kinopoisk_id))
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False

    if dry_run:
        return None, True

    try:
        film = await _create_film_from_kinopoisk(session, row=row, client=kp_client)
    except KinopoiskClientError as exc:
        _log.warning(
            '[rank %s] kp=%s «%s» — Kinopoisk fetch failed: %s',
            row.rank,
            row.kinopoisk_id,
            row.letterboxd_name,
            exc,
        )
        return None, True

    return film, True


async def _upsert_collection_film(
    session,
    *,
    collection_id: int,
    film_id: int,
    row: SeedRow,
    dry_run: bool,
) -> str:
    """Return ``inserted``, ``updated``, or ``unchanged``."""
    existing = (
        await session.execute(
            select(CollectionFilm).where(
                CollectionFilm.collection_id == collection_id,
                CollectionFilm.film_id == film_id,
            ),
        )
    ).scalar_one_or_none()

    if existing is not None:
        if existing.sort_order != row.rank or existing.seed_imdb_id != row.imdb_id:
            if not dry_run:
                existing.sort_order = row.rank
                existing.seed_imdb_id = row.imdb_id
            return 'updated'
        return 'unchanged'

    if dry_run:
        return 'inserted'

    session.add(
        CollectionFilm(
            collection_id=collection_id,
            film_id=film_id,
            sort_order=row.rank,
            seed_imdb_id=row.imdb_id,
        ),
    )
    return 'inserted'


async def _run(
    *,
    dry_run: bool,
    limit: int | None,
    sleep_s: float,
    manifest_path: Path,
) -> SeedSummary:
    _configure_script_logging()
    factory = get_session_factory()
    summary = SeedSummary()
    content_updated_at = dt.datetime.now(dt.UTC)

    all_rows, summary.skipped_todo = _load_manifest(manifest_path)
    rows = all_rows[:limit] if limit is not None else all_rows
    total = len(rows)

    _log.info('=== Seed Letterboxd Top 500 ===')
    _log.info('Manifest: %s', manifest_path)
    _log.info('Rows in manifest (resolved kp id): %s', len(all_rows))
    _log.info('Skipped TODO rows: %s', summary.skipped_todo)
    _log.info('Processing: %s', total)
    _log.info('Dry-run: %s', dry_run)
    if total == 0:
        _log.info('Nothing to do.')
        return summary

    if not dry_run:
        async with factory() as session:
            await _get_or_create_collection(session, content_updated_at=content_updated_at)
            await session.commit()

    kp_client = KinopoiskClient()

    for index, row in enumerate(rows, start=1):
        created_via_api = False
        try:
            async with factory() as session:
                if dry_run:
                    film, created_via_api = await _ensure_film(
                        session,
                        row=row,
                        kp_client=kp_client,
                        dry_run=True,
                    )
                    if created_via_api and film is None:
                        summary.created_films += 1
                    elif film is not None:
                        summary.reused_films += 1
                    summary.linked += 1
                    continue

                collection = await _get_or_create_collection(
                    session,
                    content_updated_at=content_updated_at,
                )
                film, created_via_api = await _ensure_film(
                    session,
                    row=row,
                    kp_client=kp_client,
                    dry_run=False,
                )
                if film is None:
                    summary.errors += 1
                    await session.rollback()
                    continue

                if created_via_api:
                    summary.created_films += 1
                else:
                    summary.reused_films += 1

                link_status = await _upsert_collection_film(
                    session,
                    collection_id=collection.id,
                    film_id=film.id,
                    row=row,
                    dry_run=False,
                )
                summary.linked += 1
                if link_status == 'updated':
                    summary.updated_links += 1

                await session.commit()
        except Exception as exc:
            summary.errors += 1
            _log.warning(
                '[%s/%s rank %s] kp=%s — ERROR: %s',
                index,
                total,
                row.rank,
                row.kinopoisk_id,
                exc,
            )

        if index % 25 == 0 or index == total:
            _log.info(
                '--- checkpoint %s/%s | created=%s reused=%s linked=%s err=%s ---',
                index,
                total,
                summary.created_films,
                summary.reused_films,
                summary.linked,
                summary.errors,
            )

        if created_via_api and not dry_run:
            await asyncio.sleep(sleep_s)

    if not dry_run:
        async with factory() as session:
            collection = (
                await session.execute(
                    select(Collection).where(Collection.slug == _COLLECTION_SLUG),
                )
            ).scalar_one()
            film_count = int(
                (
                    await session.execute(
                        select(func.count(CollectionFilm.id)).where(
                            CollectionFilm.collection_id == collection.id,
                        ),
                    )
                ).scalar_one(),
            )
            collection.film_count = film_count
            collection.content_updated_at = content_updated_at
            await session.commit()
            _log.info('Collection film_count=%s', film_count)

    _log.info('=== Done ===')
    _log.info('created_films=%s', summary.created_films)
    _log.info('reused_films=%s', summary.reused_films)
    _log.info('linked=%s', summary.linked)
    _log.info('updated_links=%s', summary.updated_links)
    _log.info('skipped_todo=%s', summary.skipped_todo)
    _log.info('errors=%s', summary.errors)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--sleep', type=float, default=0.2, help='seconds between KP resolves')
    parser.add_argument(
        '--manifest',
        type=Path,
        default=_MANIFEST_PATH,
        help='path to letterboxd_top_500_kinopoisk.json',
    )
    args = parser.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            limit=args.limit,
            sleep_s=max(0.0, args.sleep),
            manifest_path=args.manifest,
        ),
    )


if __name__ == '__main__':
    main()
