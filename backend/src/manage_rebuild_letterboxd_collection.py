"""One-off rebuild: re-link all 500 Letterboxd ranks to canonical films (imdb-first).

Production:
  docker exec -w /opt/app filmony-backend python src/manage_rebuild_letterboxd_collection.py
  docker exec -w /opt/app filmony-backend python src/manage_rebuild_letterboxd_collection.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

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

_COLLECTION_SLUG = 'letterboxd-top-500'
_MANIFEST_PATH = Path(__file__).resolve().parent / 'data/curated/letterboxd_top_500_kinopoisk.json'
_SLEEP_S = 0.25


@dataclass(frozen=True, slots=True)
class ManifestRow:
    rank: int
    letterboxd_name: str
    year: int | None
    kinopoisk_id: int
    imdb_id: str | None


@dataclass
class RebuildSummary:
    resolved_via_imdb: int = 0
    created_films: int = 0
    reused_films: int = 0
    linked: int = 0
    errors: int = 0


def _load_manifest(path: Path) -> list[ManifestRow]:
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding='utf-8'))
    rows: list[ManifestRow] = []
    for item in raw:
        kp = item.get('kinopoisk_id')
        if kp == 'TODO' or kp is None:
            raise ValueError(f'rank {item.get("rank")}: unresolved kinopoisk_id')
        rows.append(
            ManifestRow(
                rank=int(item['rank']),
                letterboxd_name=str(item.get('letterboxd_name') or ''),
                year=int(item['year']) if item.get('year') is not None else None,
                kinopoisk_id=int(kp),
                imdb_id=str(item['imdb_id']).strip() if item.get('imdb_id') else None,
            ),
        )
    rows.sort(key=lambda r: r.rank)
    if len(rows) != 500:
        raise ValueError(f'expected 500 manifest rows, got {len(rows)}')
    return rows


async def _kinopoisk_id_for_imdb(client: httpx.AsyncClient, imdb_id: str) -> int | None:
    base = settings.kinopoisk.base_url.rstrip('/')
    url = f'{base}/v2.2/films'
    headers = {'X-API-KEY': settings.kinopoisk.api_key}
    for attempt in range(5):
        resp = await client.get(url, params={'imdbId': imdb_id, 'page': 1}, headers=headers)
        if resp.status_code == 429:
            await asyncio.sleep(1.0 + attempt)
            continue
        if resp.status_code != 200:
            return None
        payload = resp.json()
        items = payload.get('items') if isinstance(payload, dict) else None
        if not isinstance(items, list) or not items:
            return None
        first = items[0]
        if not isinstance(first, dict):
            return None
        film_id = first.get('kinopoiskId') or first.get('filmId')
        return int(film_id) if isinstance(film_id, int) else None
    return None


def _poster_is_placeholder(url: str | None) -> bool:
    if not url:
        return True
    return 'no-poster' in url.lower()


async def _pick_best_film(session, candidates: list[Film]) -> Film | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    best: Film | None = None
    best_score = -1
    for film in candidates:
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
        if not _poster_is_placeholder(film.poster_url):
            score += 5
        if film.imdb_id:
            score += 2
        if score > best_score:
            best_score = score
            best = film
    return best


async def _find_film(session, *, imdb_id: str | None, kinopoisk_id: int) -> Film | None:
    if imdb_id:
        by_imdb = (
            (await session.execute(select(Film).where(Film.imdb_id == imdb_id))).scalars().all()
        )
        picked = await _pick_best_film(session, list(by_imdb))
        if picked is not None:
            return picked
    by_kp = (
        (await session.execute(select(Film).where(Film.kinopoisk_id == kinopoisk_id)))
        .scalars()
        .all()
    )
    return await _pick_best_film(session, list(by_kp))


async def _create_film(session, *, kinopoisk_id: int, kp_client: KinopoiskClient) -> Film:
    payload = await kp_client.get_film(kinopoisk_id)
    film = Film(
        kinopoisk_id=payload.kinopoisk_id,
        title=payload.title,
        year=payload.year,
        poster_url=payload.poster_url,
        genres=payload.genres,
        countries=payload.countries,
        short_description=payload.short_description,
        description=payload.description,
        imdb_id=payload.imdb_id,
    )
    session.add(film)
    await session.flush()
    return film


async def _resolve_kinopoisk_id(
    http: httpx.AsyncClient,
    row: ManifestRow,
    summary: RebuildSummary,
) -> int:
    if row.imdb_id:
        resolved = await _kinopoisk_id_for_imdb(http, row.imdb_id)
        if resolved is not None:
            if resolved != row.kinopoisk_id:
                _log.info(
                    '[rank %s] imdb %s: manifest kp=%s -> resolved kp=%s',
                    row.rank,
                    row.imdb_id,
                    row.kinopoisk_id,
                    resolved,
                )
            summary.resolved_via_imdb += 1
            return resolved
        await asyncio.sleep(_SLEEP_S)
    return row.kinopoisk_id


async def _ensure_film_for_row(
    session,
    *,
    row: ManifestRow,
    kinopoisk_id: int,
    kp_client: KinopoiskClient,
    summary: RebuildSummary,
    dry_run: bool,
) -> Film | None:
    film = await _find_film(session, imdb_id=row.imdb_id, kinopoisk_id=kinopoisk_id)
    if film is not None:
        summary.reused_films += 1
        return film
    if dry_run:
        summary.created_films += 1
        return None
    try:
        film = await _create_film(session, kinopoisk_id=kinopoisk_id, kp_client=kp_client)
    except KinopoiskClientError as exc:
        _log.warning('[rank %s] kp=%s create failed: %s', row.rank, kinopoisk_id, exc)
        summary.errors += 1
        return None
    summary.created_films += 1
    await asyncio.sleep(_SLEEP_S)
    return film


async def _run(*, dry_run: bool) -> RebuildSummary:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    rows = _load_manifest(_MANIFEST_PATH)
    summary = RebuildSummary()
    factory = get_session_factory()
    kp_client = KinopoiskClient()

    links: list[tuple[int, int, str | None]] = []

    async with httpx.AsyncClient(timeout=8.0) as http:
        for row in rows:
            try:
                async with factory() as session:
                    kinopoisk_id = await _resolve_kinopoisk_id(http, row, summary)
                    film = await _ensure_film_for_row(
                        session,
                        row=row,
                        kinopoisk_id=kinopoisk_id,
                        kp_client=kp_client,
                        summary=summary,
                        dry_run=dry_run,
                    )
                    if film is None and not dry_run:
                        continue
                    if film is not None:
                        links.append((row.rank, film.id, row.imdb_id))
                    elif dry_run:
                        links.append((row.rank, -row.rank, row.imdb_id))
                    await session.commit()
            except Exception as exc:
                summary.errors += 1
                _log.warning('[rank %s] ERROR: %s', row.rank, exc)

    if len(links) != 500:
        raise RuntimeError(
            f'expected 500 resolved links, got {len(links)} (errors={summary.errors})'
        )

    film_ids = [fid for _, fid, _ in links if fid > 0]
    if len(set(film_ids)) != len(film_ids):
        dupes = len(film_ids) - len(set(film_ids))
        raise RuntimeError(f'duplicate film_ids in rebuild: {dupes}')

    if dry_run:
        _log.info('DRY RUN: would write %s links, unique films=%s', len(links), len(set(film_ids)))
        return summary

    async with factory() as session:
        collection = (
            await session.execute(select(Collection).where(Collection.slug == _COLLECTION_SLUG))
        ).scalar_one()
        collection_id = collection.id

        await session.execute(
            delete(CollectionFilm).where(CollectionFilm.collection_id == collection_id),
        )

        for rank, film_id, seed_imdb in links:
            session.add(
                CollectionFilm(
                    collection_id=collection_id,
                    film_id=film_id,
                    sort_order=rank,
                    seed_imdb_id=seed_imdb,
                ),
            )

        collection.film_count = 500
        await session.commit()
        _log.info('collection %s rebuilt: film_count=500 links=%s', collection.slug, len(links))

    async with factory() as session:
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
            coll = (
                await session.execute(select(Collection).where(Collection.id == collection_id))
            ).scalar_one()
            progress = await RefreshUserCollectionProgressService.build(session).execute(
                user_id,
                coll.id,
            )
            _log.info(
                'progress user=%s: %s/%s', user_id, progress.rated_count, progress.total_count
            )

    _log.info('=== Done ===')
    _log.info('resolved_via_imdb=%s', summary.resolved_via_imdb)
    _log.info(
        'created_films=%s reused_films=%s errors=%s',
        summary.created_films,
        summary.reused_films,
        summary.errors,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    asyncio.run(_run(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
