"""Seed evergreen Letterboxd curated lists (MCU, one-million-watched) from embedded film rows.

Source manifests (git-tracked):
  ``src/data/curated/letterboxd_mcu_kinopoisk_full.json``
  ``src/data/curated/letterboxd_one_million_watched_kinopoisk_full.json``

Each manifest row includes a pre-resolved ``film`` dict — no Kinopoisk API calls.

Direct CLI (inside container, ``-w /opt/app``):

  python src/manage_seed_letterboxd_list_full.py [--list mcu|one_million_watched|all]
      [--dry-run] [--limit N] [--manifest PATH]

Idempotent: safe to re-run; upserts ``Collection`` / ``CollectionFilm`` only (no user progress).
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

_log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / 'data/curated'

LIST_CONFIGS: dict[str, dict[str, Any]] = {
    'mcu': {
        'slug': 'letterboxd-mcu',
        'title': 'Киновселенная Marvel',
        'description': (
            'Все фильмы MCU в порядке выхода — смотрите и отмечайте, сколько уже в копилке.'
        ),
        'manifest': _DATA_DIR / 'letterboxd_mcu_kinopoisk_full.json',
    },
    'one_million_watched': {
        'slug': 'letterboxd-one-million-watched',
        'title': 'Letterboxd: миллион просмотров',
        'description': (
            'Фильмы, которые на Letterboxd посмотрели больше миллиона раз. Сколько уже оценили?'
        ),
        'manifest': _DATA_DIR / 'letterboxd_one_million_watched_kinopoisk_full.json',
    },
    'horror_250': {
        'slug': 'letterboxd-horror-250',
        'title': 'Letterboxd: топ-250 ужасов',
        'description': (
            'Официальный топ-250 фильмов ужасов Letterboxd (Official Top 250 Horror Films).'
        ),
        'manifest': _DATA_DIR / 'letterboxd_horror_250_kinopoisk_full.json',
    },
    'samurai_100': {
        'slug': 'letterboxd-samurai-100',
        'title': 'Letterboxd: 100 самурайских фильмов',
        'description': (
            'Официальный топ-100 самурайских фильмов Letterboxd (Official Top 100 Samurai Films).'
        ),
        'manifest': _DATA_DIR / 'letterboxd_samurai_100_kinopoisk_full.json',
    },
}

_QUIET_HTTP_LOGGERS = ('httpx', 'httpcore', 'hpack')


@dataclass(frozen=True, slots=True)
class SeedRow:
    rank: int
    letterboxd_name: str
    year: int | None
    kinopoisk_id: int
    imdb_id: str | None
    film: dict[str, Any]


@dataclass
class SeedSummary:
    created_films: int = 0
    reused_films: int = 0
    linked: int = 0
    updated_links: int = 0
    skipped_invalid: int = 0
    errors: int = 0


def _configure_script_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    for name in _QUIET_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _load_manifest(path: Path) -> tuple[list[SeedRow], int]:
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
    skipped_invalid = 0
    rows: list[SeedRow] = []
    for item in raw:
        kp = item.get('kinopoisk_id')
        film_data = item.get('film')
        if not isinstance(kp, int) or not isinstance(film_data, dict):
            skipped_invalid += 1
            continue
        imdb = item.get('imdb_id')
        rows.append(
            SeedRow(
                rank=int(item['rank']),
                letterboxd_name=str(item.get('name') or item.get('letterboxd_name') or ''),
                year=int(item['year']) if item.get('year') is not None else None,
                kinopoisk_id=kp,
                imdb_id=str(imdb) if imdb else None,
                film=film_data,
            ),
        )
    rows.sort(key=lambda r: r.rank)
    return rows, skipped_invalid


def _create_film_from_embedded(*, row: SeedRow) -> Film:
    film_data = row.film
    imdb_id = film_data.get('imdb_id') or row.imdb_id
    year_raw = film_data.get('year')
    year = int(year_raw) if year_raw is not None else row.year
    genres = film_data.get('genres')
    countries = film_data.get('countries')
    return Film(
        kinopoisk_id=int(film_data.get('kinopoisk_id', row.kinopoisk_id)),
        title=str(film_data['title']),
        year=year,
        poster_url=film_data.get('poster_url'),
        genres=list(genres) if isinstance(genres, list) else [],
        countries=list(countries) if isinstance(countries, list) else [],
        short_description=film_data.get('short_description'),
        description=film_data.get('description'),
        imdb_id=str(imdb_id) if imdb_id else None,
    )


async def _get_or_create_collection(
    session,
    *,
    slug: str,
    title: str,
    description: str,
    content_updated_at: dt.datetime,
) -> Collection:
    existing = (
        await session.execute(select(Collection).where(Collection.slug == slug))
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.kind = CollectionKind.evergreen
        existing.is_active = True
        existing.season_year = None
        existing.content_updated_at = content_updated_at
        return existing

    collection = Collection(
        slug=slug,
        kind=CollectionKind.evergreen,
        title=title,
        description=description,
        season_year=None,
        is_active=True,
        film_count=0,
        content_updated_at=content_updated_at,
    )
    session.add(collection)
    await session.flush()
    return collection


async def _ensure_film(
    session,
    *,
    row: SeedRow,
    dry_run: bool,
) -> tuple[Film | None, bool]:
    """Return (film, created_from_embedded)."""
    existing = (
        await session.execute(select(Film).where(Film.kinopoisk_id == row.kinopoisk_id))
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False

    if dry_run:
        return None, True

    film = _create_film_from_embedded(row=row)
    session.add(film)
    await session.flush()
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


async def _run_list(
    *,
    list_key: str,
    slug: str,
    title: str,
    description: str,
    dry_run: bool,
    limit: int | None,
    manifest_path: Path,
) -> SeedSummary:
    _configure_script_logging()
    factory = get_session_factory()
    summary = SeedSummary()
    content_updated_at = dt.datetime.now(dt.UTC)

    all_rows, summary.skipped_invalid = _load_manifest(manifest_path)
    rows = all_rows[:limit] if limit is not None else all_rows
    total = len(rows)

    _log.info('=== Seed Letterboxd list: %s ===', list_key)
    _log.info('Collection slug: %s', slug)
    _log.info('Manifest: %s', manifest_path)
    _log.info('Rows in manifest (resolved kp id + film): %s', len(all_rows))
    _log.info('Skipped invalid rows: %s', summary.skipped_invalid)
    _log.info('Processing: %s', total)
    _log.info('Dry-run: %s', dry_run)
    if total == 0:
        _log.info('Nothing to do.')
        return summary

    if not dry_run:
        async with factory() as session:
            await _get_or_create_collection(
                session,
                slug=slug,
                title=title,
                description=description,
                content_updated_at=content_updated_at,
            )
            await session.commit()

    for index, row in enumerate(rows, start=1):
        try:
            async with factory() as session:
                if dry_run:
                    film, created = await _ensure_film(session, row=row, dry_run=True)
                    if created and film is None:
                        summary.created_films += 1
                    elif film is not None:
                        summary.reused_films += 1
                    summary.linked += 1
                    continue

                collection = await _get_or_create_collection(
                    session,
                    slug=slug,
                    title=title,
                    description=description,
                    content_updated_at=content_updated_at,
                )
                film, created = await _ensure_film(session, row=row, dry_run=False)
                if film is None:
                    summary.errors += 1
                    await session.rollback()
                    continue

                if created:
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

    if not dry_run:
        async with factory() as session:
            collection = (
                await session.execute(select(Collection).where(Collection.slug == slug))
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

    _log.info('=== Done: %s ===', list_key)
    _log.info('created_films=%s', summary.created_films)
    _log.info('reused_films=%s', summary.reused_films)
    _log.info('linked=%s', summary.linked)
    _log.info('updated_links=%s', summary.updated_links)
    _log.info('skipped_invalid=%s', summary.skipped_invalid)
    _log.info('errors=%s', summary.errors)
    return summary


async def _run(
    *,
    list_keys: list[str],
    dry_run: bool,
    limit: int | None,
    manifest_override: Path | None,
) -> None:
    for list_key in list_keys:
        config = LIST_CONFIGS[list_key]
        manifest_path = manifest_override or config['manifest']
        await _run_list(
            list_key=list_key,
            slug=str(config['slug']),
            title=str(config['title']),
            description=str(config['description']),
            dry_run=dry_run,
            limit=limit,
            manifest_path=manifest_path,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--list',
        choices=['mcu', 'one_million_watched', 'horror_250', 'samurai_100', 'all'],
        default='all',
        help='which curated list to seed (default: all)',
    )
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument(
        '--manifest',
        type=Path,
        default=None,
        help='override manifest path for the selected list(s)',
    )
    args = parser.parse_args()

    list_keys = list(LIST_CONFIGS.keys()) if args.list == 'all' else [args.list]

    asyncio.run(
        _run(
            list_keys=list_keys,
            dry_run=args.dry_run,
            limit=args.limit,
            manifest_override=args.manifest,
        ),
    )


if __name__ == '__main__':
    main()
