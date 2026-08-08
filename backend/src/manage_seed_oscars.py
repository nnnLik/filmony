"""Seed seasonal ``oscars-{year}`` collections from curated Kinopoisk mapping.

Source manifests (git-tracked):
  ``src/data/curated/oscars/oscars_{2020..2026}_kinopoisk.json``

Original mapping pipeline (not run in prod):
  ``.cursor/active/collections-core/collections/oscars/map_oscar_kp.py``

``is_winner`` is preserved in JSON for future badge work; ``CollectionFilm`` has no
winner column yet — winner info is not written to the DB.

Production (from repo root). Full runbook: ``.cursor/active/collections-core/PROD_SEED.md``.

  # dry-run all years
  DRY_RUN=1 make seed-oscars

  # single ceremony year
  YEAR=2024 make seed-oscars

  # apply all years (~67 films across 2020–2026)
  make seed-oscars

Direct CLI (inside container, ``-w /opt/app``):

  python src/manage_seed_oscars.py [--year 2024] [--dry-run] [--limit N] [--sleep 0.2]

Idempotent: safe to re-run; upserts ``Collection`` / ``CollectionFilm`` only (no user progress).
Bulk seed skips TMDB enrich to avoid ``ix_film_tmdb_id`` collisions; use backfill if needed.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import logging
import re
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

_CURATED_DIR = Path(__file__).resolve().parent / 'data/curated/oscars'
_MANIFEST_PATTERN = re.compile(r'^oscars_(\d{4})_kinopoisk\.json$')

_QUIET_HTTP_LOGGERS = ('httpx', 'httpcore', 'hpack')


@dataclass(frozen=True, slots=True)
class OscarSeedRow:
    sort_order: int
    name: str
    year: int | None
    kinopoisk_id: int
    imdb_id: str | None
    is_winner: bool
    ceremony_year: int


@dataclass
class YearSeedSummary:
    year: int
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


def _discover_years(curated_dir: Path) -> list[int]:
    years: list[int] = []
    for path in sorted(curated_dir.glob('oscars_*_kinopoisk.json')):
        match = _MANIFEST_PATTERN.match(path.name)
        if match is None:
            continue
        years.append(int(match.group(1)))
    return sorted(years)


def _manifest_path(curated_dir: Path, year: int) -> Path:
    return curated_dir / f'oscars_{year}_kinopoisk.json'


def _collection_slug(year: int) -> str:
    return f'oscars-{year}'


def _collection_title(year: int) -> str:
    film_year = year - 1
    return f'Оскар за {film_year}'


def _collection_description(year: int) -> str:
    film_year = year - 1
    return (
        f'Главные претенденты на лучший фильм среди картин {film_year}-го. '
        f'Церемония {year}-го — смотрите и отмечайте, кого уже оценили.'
    )


def _load_manifest(path: Path, *, ceremony_year: int) -> tuple[list[OscarSeedRow], int]:
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
    skipped_todo = sum(1 for item in raw if item.get('kinopoisk_id') == 'TODO')
    rows: list[OscarSeedRow] = []
    for item in raw:
        kp = item.get('kinopoisk_id')
        if kp == 'TODO' or kp is None:
            continue
        if not isinstance(kp, int):
            raise TypeError(
                f'invalid kinopoisk_id for sort_order {item.get("sort_order")}: {kp!r}',
            )
        imdb = item.get('imdb_id')
        rows.append(
            OscarSeedRow(
                sort_order=int(item['sort_order']),
                name=str(item.get('name') or ''),
                year=int(item['year']) if item.get('year') is not None else None,
                kinopoisk_id=kp,
                imdb_id=str(imdb) if imdb else None,
                is_winner=bool(item.get('is_winner')),
                ceremony_year=int(item.get('ceremony_year') or ceremony_year),
            ),
        )
    rows.sort(key=lambda r: r.sort_order)
    return rows, skipped_todo


async def _get_or_create_collection(
    session,
    *,
    year: int,
    content_updated_at: dt.datetime,
) -> Collection:
    slug = _collection_slug(year)
    title = _collection_title(year)
    description = _collection_description(year)
    existing = (
        await session.execute(select(Collection).where(Collection.slug == slug))
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.kind = CollectionKind.seasonal
        existing.season_year = year
        existing.is_active = True
        existing.content_updated_at = content_updated_at
        return existing

    collection = Collection(
        slug=slug,
        kind=CollectionKind.seasonal,
        title=title,
        description=description,
        season_year=year,
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
    row: OscarSeedRow,
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
    row: OscarSeedRow,
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
            '[oscars-%s sort %s] kp=%s «%s» — Kinopoisk fetch failed: %s',
            row.ceremony_year,
            row.sort_order,
            row.kinopoisk_id,
            row.name,
            exc,
        )
        return None, True

    return film, True


async def _upsert_collection_film(
    session,
    *,
    collection_id: int,
    film_id: int,
    row: OscarSeedRow,
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
        if existing.sort_order != row.sort_order or existing.seed_imdb_id != row.imdb_id:
            if not dry_run:
                existing.sort_order = row.sort_order
                existing.seed_imdb_id = row.imdb_id
            return 'updated'
        return 'unchanged'

    if dry_run:
        return 'inserted'

    session.add(
        CollectionFilm(
            collection_id=collection_id,
            film_id=film_id,
            sort_order=row.sort_order,
            seed_imdb_id=row.imdb_id,
        ),
    )
    return 'inserted'


async def _seed_year(
    *,
    year: int,
    curated_dir: Path,
    dry_run: bool,
    limit: int | None,
    sleep_s: float,
) -> YearSeedSummary:
    factory = get_session_factory()
    summary = YearSeedSummary(year=year)
    content_updated_at = dt.datetime.now(dt.UTC)
    manifest_path = _manifest_path(curated_dir, year)

    if not manifest_path.is_file():
        raise FileNotFoundError(f'missing manifest: {manifest_path}')

    all_rows, summary.skipped_todo = _load_manifest(manifest_path, ceremony_year=year)
    rows = all_rows[:limit] if limit is not None else all_rows
    total = len(rows)
    slug = _collection_slug(year)

    _log.info('=== Seed Oscars %s (%s) ===', year, slug)
    _log.info('Manifest: %s', manifest_path)
    _log.info('Rows in manifest (resolved kp id): %s', len(all_rows))
    _log.info('Skipped TODO rows: %s', summary.skipped_todo)
    _log.info('Processing: %s', total)
    _log.info('Dry-run: %s', dry_run)

    if total == 0:
        _log.info('Nothing to do for %s.', year)
        return summary

    if not dry_run:
        async with factory() as session:
            await _get_or_create_collection(
                session, year=year, content_updated_at=content_updated_at
            )
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
                    year=year,
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
                '[%s/%s oscars-%s sort %s] kp=%s — ERROR: %s',
                index,
                total,
                year,
                row.sort_order,
                row.kinopoisk_id,
                exc,
            )

        if index % 10 == 0 or index == total:
            _log.info(
                '--- %s checkpoint %s/%s | created=%s reused=%s linked=%s err=%s ---',
                year,
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
                    select(Collection).where(Collection.slug == slug),
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
            _log.info('Collection %s film_count=%s', slug, film_count)

    _log.info(
        '=== Done oscars-%s | created=%s reused=%s linked=%s updated=%s errors=%s ===',
        year,
        summary.created_films,
        summary.reused_films,
        summary.linked,
        summary.updated_links,
        summary.errors,
    )
    return summary


async def _run(
    *,
    years: list[int],
    curated_dir: Path,
    dry_run: bool,
    limit: int | None,
    sleep_s: float,
) -> list[YearSeedSummary]:
    _configure_script_logging()
    summaries: list[YearSeedSummary] = []

    _log.info('=== Seed Oscars collections ===')
    _log.info('Curated dir: %s', curated_dir)
    _log.info('Years: %s', years)
    _log.info('Dry-run: %s', dry_run)

    for year in years:
        summaries.append(
            await _seed_year(
                year=year,
                curated_dir=curated_dir,
                dry_run=dry_run,
                limit=limit,
                sleep_s=sleep_s,
            ),
        )

    total_linked = sum(s.linked for s in summaries)
    total_errors = sum(s.errors for s in summaries)
    _log.info('=== All years done | linked=%s errors=%s ===', total_linked, total_errors)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--year',
        type=int,
        default=None,
        help='ceremony year (default: all manifests in curated/oscars/)',
    )
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None, help='max rows per year')
    parser.add_argument('--sleep', type=float, default=0.2, help='seconds between KP resolves')
    parser.add_argument(
        '--curated-dir',
        type=Path,
        default=_CURATED_DIR,
        help='directory with oscars_{year}_kinopoisk.json manifests',
    )
    args = parser.parse_args()

    available = _discover_years(args.curated_dir)
    if not available:
        raise SystemExit(f'no manifests found in {args.curated_dir}')

    if args.year is not None:
        if args.year not in available:
            raise SystemExit(
                f'year {args.year} not found; available: {", ".join(str(y) for y in available)}',
            )
        years = [args.year]
    else:
        years = available

    asyncio.run(
        _run(
            years=years,
            curated_dir=args.curated_dir,
            dry_run=args.dry_run,
            limit=args.limit,
            sleep_s=max(0.0, args.sleep),
        ),
    )


if __name__ == '__main__':
    main()
