"""Rebuild Letterboxd Top 500 on prod: 500 unique films, imdb→kp, no empty shells.

python src/manage_rebuild_letterboxd_collection.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import delete, func, select

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
_SLEEP_S = 0.3


@dataclass(frozen=True, slots=True)
class ManifestRow:
    rank: int
    letterboxd_name: str
    year: int | None
    kinopoisk_id: int
    imdb_id: str | None


@dataclass
class RankPlan:
    rank: int
    letterboxd_name: str
    imdb_id: str | None
    kinopoisk_id: int
    resolve_source: str
    film_id: int | None = None
    film_title: str | None = None
    film_year: int | None = None
    created: bool = False


@dataclass
class RebuildSummary:
    from_db: int = 0
    from_api: int = 0
    from_manifest: int = 0
    created_films: int = 0
    reused_films: int = 0
    errors: list[str] = field(default_factory=list)


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


def _poster_ok(url: str | None) -> bool:
    return bool(url) and 'no-poster' not in url.lower()


async def _api_kp_for_imdb(client: httpx.AsyncClient, imdb_id: str) -> int | None:
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


async def _score_film(session, film: Film) -> int:
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
    if _poster_ok(film.poster_url):
        score += 5
    if film.imdb_id:
        score += 2
    return score


async def _get_or_create_by_kp(
    session,
    *,
    kinopoisk_id: int,
    imdb_id: str | None,
    kp_client: KinopoiskClient,
    dry_run: bool,
    summary: RebuildSummary,
) -> Film | None:
    candidates = (
        (await session.execute(select(Film).where(Film.kinopoisk_id == kinopoisk_id)))
        .scalars()
        .all()
    )
    if candidates:
        best_score = -1
        best_film: Film | None = None
        for film in candidates:
            score = await _score_film(session, film)
            if score > best_score:
                best_score = score
                best_film = film
        assert best_film is not None
        if imdb_id and not best_film.imdb_id and not dry_run:
            best_film.imdb_id = imdb_id
        summary.reused_films += 1
        return best_film

    if dry_run:
        summary.created_films += 1
        return None

    try:
        payload = await kp_client.get_film(kinopoisk_id)
    except KinopoiskClientError as exc:
        summary.errors.append(f'kp={kinopoisk_id} create failed: {exc}')
        return None

    film = Film(
        kinopoisk_id=payload.kinopoisk_id,
        title=payload.title,
        year=payload.year,
        poster_url=payload.poster_url,
        genres=payload.genres,
        countries=payload.countries,
        short_description=payload.short_description,
        description=payload.description,
        imdb_id=payload.imdb_id or imdb_id,
    )
    session.add(film)
    await session.flush()
    summary.created_films += 1
    await asyncio.sleep(_SLEEP_S)
    return film


async def _run(*, dry_run: bool) -> RebuildSummary:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    rows = _load_manifest(_MANIFEST_PATH)
    summary = RebuildSummary()
    factory = get_session_factory()
    kp_client = KinopoiskClient()

    _log.info('=== STAGE 1/4: resolve kinopoisk ids (imdb-first) ===')

    async with factory() as session:
        db_films = (
            await session.execute(
                select(Film.imdb_id, Film.kinopoisk_id).where(Film.imdb_id.is_not(None)),
            )
        ).all()
    imdb_to_kps: dict[str, set[int]] = defaultdict(set)
    for imdb, kp in db_films:
        imdb_to_kps[imdb].add(int(kp))

    plans: list[RankPlan] = []
    need_api: list[ManifestRow] = []

    for row in rows:
        if row.imdb_id and len(imdb_to_kps.get(row.imdb_id, ())) == 1:
            kp = next(iter(imdb_to_kps[row.imdb_id]))
            plans.append(
                RankPlan(
                    rank=row.rank,
                    letterboxd_name=row.letterboxd_name,
                    imdb_id=row.imdb_id,
                    kinopoisk_id=kp,
                    resolve_source='db',
                ),
            )
            summary.from_db += 1
        else:
            need_api.append(row)

    _log.info(
        'cached from DB (unique imdb→kp): %s; need API/manifest: %s', summary.from_db, len(need_api)
    )

    async with httpx.AsyncClient(timeout=8.0) as http:
        for index, row in enumerate(need_api, start=1):
            kp = row.kinopoisk_id
            source = 'manifest'
            if row.imdb_id:
                resolved = await _api_kp_for_imdb(http, row.imdb_id)
                await asyncio.sleep(_SLEEP_S)
                if resolved is not None:
                    kp = resolved
                    source = 'api'
                    summary.from_api += 1
                else:
                    summary.from_manifest += 1
            else:
                summary.from_manifest += 1
            if kp != row.kinopoisk_id:
                _log.info(
                    '[rank %s] %s: manifest kp=%s → %s kp=%s',
                    row.rank,
                    row.letterboxd_name,
                    row.kinopoisk_id,
                    source,
                    kp,
                )
            plans.append(
                RankPlan(
                    rank=row.rank,
                    letterboxd_name=row.letterboxd_name,
                    imdb_id=row.imdb_id,
                    kinopoisk_id=kp,
                    resolve_source=source,
                ),
            )
            if index % 25 == 0 or index == len(need_api):
                _log.info('--- resolve progress %s/%s ---', index, len(need_api))

    plans.sort(key=lambda p: p.rank)
    by_kp: dict[int, list[RankPlan]] = defaultdict(list)
    for plan in plans:
        by_kp[plan.kinopoisk_id].append(plan)
    collisions = {kp: items for kp, items in by_kp.items() if len(items) > 1}
    if collisions:
        for kp, items in collisions.items():
            msg = f'kp collision {kp}: ' + ', '.join(
                f'rank {p.rank} «{p.letterboxd_name}»' for p in items
            )
            summary.errors.append(msg)
            _log.error(msg)
        raise RuntimeError(f'{len(collisions)} kp collisions — cannot build unique 500')

    _log.info('resolved unique kp: %s / 500', len(by_kp))

    _log.info('=== STAGE 2/4: ensure Film rows (by kinopoisk_id) ===')
    filled: list[RankPlan] = []
    for index, plan in enumerate(plans, start=1):
        async with factory() as session:
            film = await _get_or_create_by_kp(
                session,
                kinopoisk_id=plan.kinopoisk_id,
                imdb_id=plan.imdb_id,
                kp_client=kp_client,
                dry_run=dry_run,
                summary=summary,
            )
            if film is None and not dry_run:
                summary.errors.append(f'rank {plan.rank}: no film for kp={plan.kinopoisk_id}')
                await session.rollback()
                continue
            if film is not None:
                plan.film_id = film.id
                plan.film_title = film.title
                plan.film_year = film.year
                if not _poster_ok(film.poster_url) or film.year is None:
                    _log.warning(
                        '[rank %s] weak meta film_id=%s title=%r year=%s poster_ok=%s',
                        plan.rank,
                        film.id,
                        film.title,
                        film.year,
                        _poster_ok(film.poster_url),
                    )
            filled.append(plan)
            await session.commit()
        if index % 50 == 0 or index == len(plans):
            _log.info(
                '--- ensure progress %s/%s | created=%s reused=%s err=%s ---',
                index,
                len(plans),
                summary.created_films,
                summary.reused_films,
                len(summary.errors),
            )

    if dry_run:
        film_ids = [p.film_id for p in filled if p.film_id is not None]
        _log.info(
            'DRY RUN: plans=%s with_film_id=%s unique_film_ids=%s',
            len(filled),
            len(film_ids),
            len(set(film_ids)),
        )
        return summary

    missing = [p for p in filled if p.film_id is None]
    if missing or len(filled) != 500:
        raise RuntimeError(
            f'cannot rebuild: filled={len(filled)} missing_film={len(missing)} errors={summary.errors[:5]}',
        )

    film_ids = [p.film_id for p in filled if p.film_id is not None]
    if len(set(film_ids)) != 500:
        by_fid: dict[int, list[int]] = defaultdict(list)
        for p in filled:
            if p.film_id is not None:
                by_fid[p.film_id].append(p.rank)
        dups = {fid: ranks for fid, ranks in by_fid.items() if len(ranks) > 1}
        raise RuntimeError(f'duplicate film_ids: {dups}')

    _log.info('=== STAGE 3/4: rewrite collection_film (exactly 500) ===')
    collection_id: int
    async with factory() as session:
        collection = (
            await session.execute(select(Collection).where(Collection.slug == _COLLECTION_SLUG))
        ).scalar_one()
        collection_id = int(collection.id)
        await session.execute(
            delete(CollectionFilm).where(CollectionFilm.collection_id == collection_id),
        )
        for plan in filled:
            assert plan.film_id is not None
            session.add(
                CollectionFilm(
                    collection_id=collection_id,
                    film_id=plan.film_id,
                    sort_order=plan.rank,
                    seed_imdb_id=plan.imdb_id,
                ),
            )
        collection.film_count = 500
        await session.commit()
        _log.info('collection %s: film_count=500', collection.slug)

    _log.info('=== STAGE 4/4: backfill user progress ===')
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
    _log.info('users to refresh: %s', len(user_ids))
    for user_id in user_ids:
        async with factory() as session:
            progress = await RefreshUserCollectionProgressService.build(session).execute(
                user_id,
                collection_id,
            )
            _log.info('progress %s: %s/%s', user_id, progress.rated_count, progress.total_count)

    weak = [p for p in filled if p.film_year is None]
    _log.info('=== Letterboxd rebuild DONE ===')
    _log.info('links=500 unique_films=500')
    _log.info(
        'resolve: db=%s api=%s manifest=%s | created=%s reused=%s | weak_year=%s errors=%s',
        summary.from_db,
        summary.from_api,
        summary.from_manifest,
        summary.created_films,
        summary.reused_films,
        len(weak),
        len(summary.errors),
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    asyncio.run(_run(dry_run=args.dry_run))


if __name__ == '__main__':
    main()
