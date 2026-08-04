"""Compare Kinopoisk vs TMDB director/franchise metadata on KP-enriched films."""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import unicodedata

from sqlalchemy import select

from core.database import get_session_factory
from models.film import Film
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.tmdb.tmdb_mapping import gamification_preview_from_movie, normalize_imdb_id
from providers.tmdb.tmdb_movie_dto import movie_detail_from_dict
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService

_log = logging.getLogger(__name__)


def _normalize_director_name(name: str | None) -> str:
    if name is None:
        return ''
    text = unicodedata.normalize('NFKD', name.strip().lower())
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())


async def _compare_film(
    film: Film,
    *,
    allow_kp_imdb_lookup: bool,
) -> tuple[bool, bool]:
    factory = get_session_factory()
    kp_transport = KinopoiskProviderTransport() if allow_kp_imdb_lookup else None
    syncer = SyncFilmFromTmdbService.build(kinopoisk_transport=kp_transport)
    async with factory() as session:
        row = await session.get(Film, film.id)
        if row is None:
            return False, False
        result = await syncer.execute(
            session,
            row,
            allow_kp_imdb_lookup=allow_kp_imdb_lookup,
        )
        await session.commit()
        if not result.synced:
            return False, False

        snapshot = row.tmdb_detail_snapshot_json
        if not isinstance(snapshot, dict):
            return False, False

        preview = gamification_preview_from_movie(
            movie_detail_from_dict(snapshot),
            kinopoisk_id=row.kinopoisk_id,
        )
        kp_name = _normalize_director_name(row.primary_director_name)
        tmdb_name = _normalize_director_name(preview.primary_director_name)
        name_match = kp_name != '' and kp_name == tmdb_name
        _log.info(
            'kp=%s title=%r kp_director=%r tmdb_director=%r name_match=%s '
            'kp_franchise=%s tmdb_franchise=%s imdb=%s',
            row.kinopoisk_id,
            row.title,
            row.primary_director_name,
            preview.primary_director_name,
            name_match,
            row.franchise_key,
            preview.franchise_key,
            normalize_imdb_id(row.imdb_id),
        )
        return True, name_match


async def _run(
    *,
    dry_run: bool,
    sleep_s: float,
    limit: int | None,
    allow_kp_imdb_lookup: bool,
) -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    factory = get_session_factory()
    q = select(Film).where(Film.primary_director_kinopoisk_id.is_not(None)).order_by(Film.id.asc())
    if limit is not None:
        q = q.limit(limit)
    async with factory() as session:
        films: list[Film] = list((await session.execute(q)).scalars().all())

    matched = mismatched = missing_tmdb = 0
    for film in films:
        if dry_run:
            _log.info(
                'dry-run compare kp=%s kp_director=%s franchise=%s imdb=%s',
                film.kinopoisk_id,
                film.primary_director_name,
                film.franchise_key,
                film.imdb_id,
            )
        else:
            synced, name_match = await _compare_film(
                film,
                allow_kp_imdb_lookup=allow_kp_imdb_lookup,
            )
            if not synced:
                missing_tmdb += 1
            elif name_match:
                matched += 1
            else:
                mismatched += 1
        await asyncio.sleep(sleep_s)

    _log.info(
        'compare done total=%s matched=%s mismatched=%s missing_tmdb=%s dry_run=%s',
        len(films),
        matched,
        mismatched,
        missing_tmdb,
        dry_run,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--sleep', type=float, default=0.25)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--allow-kp-imdb-lookup', action='store_true')
    args = p.parse_args()
    asyncio.run(
        _run(
            dry_run=args.dry_run,
            sleep_s=max(0.0, args.sleep),
            limit=args.limit,
            allow_kp_imdb_lookup=args.allow_kp_imdb_lookup,
        )
    )


if __name__ == '__main__':
    main()
