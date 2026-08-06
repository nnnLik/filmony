"""Refresh weak film metadata (year/poster) for Letterboxd collection members.

python src/manage_refresh_collection_film_meta.py [--slug letterboxd-top-500]
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import or_, select

from core.database import get_session_factory
from models.collection import Collection
from models.collection_film import CollectionFilm
from models.film import Film
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError

_log = logging.getLogger(__name__)
_SLEEP_S = 0.25


def _poster_weak(url: str | None) -> bool:
    return not url or 'no-poster' in url.lower()


async def _run(*, slug: str) -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    factory = get_session_factory()
    kp = KinopoiskClient()

    async with factory() as session:
        collection = (
            await session.execute(select(Collection).where(Collection.slug == slug))
        ).scalar_one()
        rows = (
            await session.execute(
                select(CollectionFilm.sort_order, Film)
                .join(Film, Film.id == CollectionFilm.film_id)
                .where(
                    CollectionFilm.collection_id == collection.id,
                    or_(
                        Film.year.is_(None),
                        Film.poster_url.is_(None),
                        Film.poster_url.ilike('%no-poster%'),
                    ),
                )
                .order_by(CollectionFilm.sort_order),
            )
        ).all()

    _log.info('weak films in %s: %s', slug, len(rows))
    fixed = 0
    failed = 0
    for index, (sort_order, film_snapshot) in enumerate(rows, start=1):
        film_id = film_snapshot.id
        kp_id = film_snapshot.kinopoisk_id
        async with factory() as session:
            film = (await session.execute(select(Film).where(Film.id == film_id))).scalar_one()
            try:
                payload = await kp.get_film(kp_id)
            except KinopoiskClientError as exc:
                failed += 1
                _log.warning('[rank %s] kp=%s refresh failed: %s', sort_order, kp_id, exc)
                continue
            before = (film.year, _poster_weak(film.poster_url), film.title)
            film.title = payload.title
            film.year = payload.year
            film.poster_url = payload.poster_url
            film.genres = payload.genres
            film.countries = payload.countries
            if payload.short_description:
                film.short_description = payload.short_description
            if payload.description:
                film.description = payload.description
            if payload.imdb_id and not film.imdb_id:
                film.imdb_id = payload.imdb_id
            await session.commit()
            after = (film.year, _poster_weak(film.poster_url), film.title)
            fixed += 1
            _log.info(
                '[rank %s] film_id=%s kp=%s %s → year=%s poster_weak=%s title=%r',
                sort_order,
                film_id,
                kp_id,
                before,
                after[0],
                after[1],
                after[2],
            )
        await asyncio.sleep(_SLEEP_S)
        if index % 10 == 0:
            _log.info('--- refresh %s/%s ---', index, len(rows))

    _log.info('=== meta refresh DONE fixed=%s failed=%s ===', fixed, failed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slug', default='letterboxd-top-500')
    args = parser.parse_args()
    asyncio.run(_run(slug=args.slug))


if __name__ == '__main__':
    main()
