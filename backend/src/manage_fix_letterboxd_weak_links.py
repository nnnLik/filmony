"""Force re-resolve weak Letterboxd ranks via Kinopoisk imdbId API (ignore bad DB cache).

python src/manage_fix_letterboxd_weak_links.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import httpx
from sqlalchemy import func, select

from conf import settings
from core.database import get_session_factory
from models.collection import Collection
from models.collection_film import CollectionFilm
from models.film import Film
from models.user_card import UserCard
from services.collections.meaningful_rated_card import meaningful_rated_card_criteria
from services.collections.refresh_user_collection_progress import (
    RefreshUserCollectionProgressService,
)
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError

_log = logging.getLogger(__name__)
_SLUG = 'letterboxd-top-500'
_MANIFEST = Path(__file__).resolve().parent / 'data/curated/letterboxd_top_500_kinopoisk.json'
_SLEEP = 0.3


def _poster_weak(url: str | None) -> bool:
    return not url or 'no-poster' in url.lower()


async def _api_kp(client: httpx.AsyncClient, imdb_id: str) -> int | None:
    base = settings.kinopoisk.base_url.rstrip('/')
    headers = {'X-API-KEY': settings.kinopoisk.api_key}
    for attempt in range(6):
        resp = await client.get(
            f'{base}/v2.2/films',
            params={'imdbId': imdb_id, 'page': 1},
            headers=headers,
        )
        if resp.status_code == 429:
            await asyncio.sleep(1.2 + attempt)
            continue
        if resp.status_code != 200:
            return None
        items = resp.json().get('items') or []
        if not items:
            return None
        kp = items[0].get('kinopoiskId') or items[0].get('filmId')
        return int(kp) if isinstance(kp, int) else None
    return None


async def _pick_film(session, kp: int) -> Film | None:
    films = (await session.execute(select(Film).where(Film.kinopoisk_id == kp))).scalars().all()
    if not films:
        return None
    best = None
    best_score = -1
    for film in films:
        rated = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(UserCard)
                    .where(UserCard.film_id == film.id, *meaningful_rated_card_criteria()),
                )
            ).scalar_one(),
        )
        score = rated * 100
        if film.year is not None:
            score += 10
        if not _poster_weak(film.poster_url):
            score += 5
        if score > best_score:
            best_score = score
            best = film
    return best


async def _create(session, kp: int, kp_client: KinopoiskClient, imdb: str | None) -> Film:
    payload = await kp_client.get_film(kp)
    film = Film(
        kinopoisk_id=payload.kinopoisk_id,
        title=payload.title,
        year=payload.year,
        poster_url=payload.poster_url,
        genres=payload.genres,
        countries=payload.countries,
        short_description=payload.short_description,
        description=payload.description,
        imdb_id=payload.imdb_id or imdb,
    )
    session.add(film)
    await session.flush()
    return film


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    manifest = {int(r['rank']): r for r in json.loads(_MANIFEST.read_text())}
    factory = get_session_factory()
    kp_client = KinopoiskClient()

    async with factory() as session:
        collection = (
            await session.execute(select(Collection).where(Collection.slug == _SLUG))
        ).scalar_one()
        collection_id = int(collection.id)
        weak = (
            await session.execute(
                select(CollectionFilm, Film)
                .join(Film, Film.id == CollectionFilm.film_id)
                .where(CollectionFilm.collection_id == collection_id)
                .where(
                    (Film.year.is_(None))
                    | (Film.poster_url.is_(None))
                    | (Film.poster_url.ilike('%no-poster%')),
                )
                .order_by(CollectionFilm.sort_order),
            )
        ).all()

    _log.info('weak links to rematch: %s', len(weak))
    used_film_ids = set()
    async with factory() as session:
        used = (
            (
                await session.execute(
                    select(CollectionFilm.film_id).where(
                        CollectionFilm.collection_id == collection_id
                    ),
                )
            )
            .scalars()
            .all()
        )
        used_film_ids = {int(x) for x in used}

    fixed = 0
    skipped = 0
    failed = 0

    async with httpx.AsyncClient(timeout=8.0) as http:
        for link, _film in weak:
            rank = int(link.sort_order)
            row = manifest.get(rank)
            if not row or not row.get('imdb_id'):
                _log.warning('[rank %s] no imdb in manifest — skip', rank)
                skipped += 1
                continue
            imdb = str(row['imdb_id'])
            resolved = await _api_kp(http, imdb)
            await asyncio.sleep(_SLEEP)
            if resolved is None:
                _log.warning('[rank %s] imdb %s not found on KP', rank, imdb)
                failed += 1
                continue

            async with factory() as session:
                link_db = (
                    await session.execute(
                        select(CollectionFilm).where(
                            CollectionFilm.collection_id == collection_id,
                            CollectionFilm.sort_order == rank,
                        ),
                    )
                ).scalar_one()
                old_film_id = int(link_db.film_id)
                old_film = (
                    await session.execute(select(Film).where(Film.id == old_film_id))
                ).scalar_one()

                new_film = await _pick_film(session, resolved)
                created = False
                if new_film is None:
                    try:
                        new_film = await _create(session, resolved, kp_client, imdb)
                        created = True
                        await asyncio.sleep(_SLEEP)
                    except KinopoiskClientError as exc:
                        failed += 1
                        _log.warning('[rank %s] create kp=%s failed: %s', rank, resolved, exc)
                        await session.rollback()
                        continue

                # if new film already used by another rank and different from current — conflict
                if new_film.id != old_film_id and new_film.id in used_film_ids:
                    # keep current if same kp already correct path unavailable
                    other = (
                        await session.execute(
                            select(CollectionFilm.sort_order).where(
                                CollectionFilm.collection_id == collection_id,
                                CollectionFilm.film_id == new_film.id,
                            ),
                        )
                    ).scalar_one_or_none()
                    _log.error(
                        '[rank %s] target film_id=%s already used by rank %s — skip',
                        rank,
                        new_film.id,
                        other,
                    )
                    failed += 1
                    await session.rollback()
                    continue

                # refresh meta always
                try:
                    payload = await kp_client.get_film(resolved)
                    new_film.title = payload.title
                    new_film.year = payload.year
                    new_film.poster_url = payload.poster_url
                    new_film.genres = payload.genres
                    new_film.countries = payload.countries
                    if payload.short_description:
                        new_film.short_description = payload.short_description
                    if payload.description:
                        new_film.description = payload.description
                    if payload.imdb_id:
                        new_film.imdb_id = payload.imdb_id
                    elif imdb:
                        new_film.imdb_id = imdb
                    await asyncio.sleep(_SLEEP)
                except KinopoiskClientError as exc:
                    _log.warning('[rank %s] meta refresh failed: %s', rank, exc)

                link_db.film_id = new_film.id
                link_db.seed_imdb_id = imdb
                used_film_ids.discard(old_film_id)
                used_film_ids.add(new_film.id)
                await session.commit()
                fixed += 1
                _log.info(
                    '[rank %s] %s: film %s kp=%s «%s» → film %s kp=%s «%s» year=%s poster_ok=%s created=%s',
                    rank,
                    row.get('letterboxd_name'),
                    old_film_id,
                    old_film.kinopoisk_id,
                    old_film.title,
                    new_film.id,
                    new_film.kinopoisk_id,
                    new_film.title,
                    new_film.year,
                    not _poster_weak(new_film.poster_url),
                    created,
                )

    # recount + progress
    async with factory() as session:
        collection = (
            await session.execute(select(Collection).where(Collection.id == collection_id))
        ).scalar_one()
        n = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(CollectionFilm)
                    .where(
                        CollectionFilm.collection_id == collection_id,
                    ),
                )
            ).scalar_one(),
        )
        uniq = int(
            (
                await session.execute(
                    select(func.count(func.distinct(CollectionFilm.film_id))).where(
                        CollectionFilm.collection_id == collection_id,
                    ),
                )
            ).scalar_one(),
        )
        collection.film_count = n
        await session.commit()
        _log.info('collection links=%s unique=%s', n, uniq)

        user_ids = (
            (
                await session.execute(
                    select(UserCard.user_id)
                    .join(CollectionFilm, CollectionFilm.film_id == UserCard.film_id)
                    .where(
                        CollectionFilm.collection_id == collection_id,
                        *meaningful_rated_card_criteria(),
                    )
                    .distinct(),
                )
            )
            .scalars()
            .all()
        )
    for user_id in user_ids:
        async with factory() as session:
            p = await RefreshUserCollectionProgressService.build(session).execute(
                user_id,
                collection_id,
            )
            _log.info('progress %s: %s/%s', user_id, p.rated_count, p.total_count)

    # remaining weak
    async with factory() as session:
        left = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(CollectionFilm)
                    .join(Film, Film.id == CollectionFilm.film_id)
                    .where(CollectionFilm.collection_id == collection_id)
                    .where(
                        (Film.year.is_(None))
                        | (Film.poster_url.is_(None))
                        | (Film.poster_url.ilike('%no-poster%')),
                    ),
                )
            ).scalar_one(),
        )
    _log.info(
        '=== rematch DONE fixed=%s skipped=%s failed=%s weak_left=%s ===',
        fixed,
        skipped,
        failed,
        left,
    )


if __name__ == '__main__':
    asyncio.run(main())
