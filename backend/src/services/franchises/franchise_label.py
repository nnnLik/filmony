"""Franchise label helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from providers.tmdb.tmdb_mapping import collection_name_from_snapshot

_KP_FRANCHISE_KEY_RE = re.compile(r'^kp_franchise:(\d+)$')
_TMDB_COLLECTION_KEY_RE = re.compile(r'^tmdb_collection:(\d+)$')


def parse_franchise_min_kinopoisk_id(franchise_key: str) -> int | None:
    match = _KP_FRANCHISE_KEY_RE.match(franchise_key.strip())
    if match is None:
        return None
    return int(match.group(1))


def parse_franchise_tmdb_collection_id(franchise_key: str) -> int | None:
    match = _TMDB_COLLECTION_KEY_RE.match(franchise_key.strip())
    if match is None:
        return None
    return int(match.group(1))


def franchise_fallback_label(franchise_key: str) -> str:
    min_id = parse_franchise_min_kinopoisk_id(franchise_key)
    if min_id is not None:
        return f'Серия #{min_id}'
    collection_id = parse_franchise_tmdb_collection_id(franchise_key)
    if collection_id is not None:
        return f'Коллекция #{collection_id}'
    return franchise_key.strip() or 'Франшиза'


async def resolve_franchise_labels(
    session: AsyncSession,
    keys: Iterable[str],
) -> dict[str, str]:
    """Resolve display labels for many franchise keys in at most two DB round-trips."""
    normalized: list[str] = []
    seen: set[str] = set()
    for key in keys:
        stripped = key.strip()
        if stripped != '' and stripped not in seen:
            seen.add(stripped)
            normalized.append(stripped)

    if not normalized:
        return {}

    labels: dict[str, str] = {}
    kp_id_by_key: dict[str, int] = {}
    kp_ids: list[int] = []

    for key in normalized:
        min_kp_id = parse_franchise_min_kinopoisk_id(key)
        if min_kp_id is not None:
            kp_id_by_key[key] = min_kp_id
            kp_ids.append(min_kp_id)

    if kp_ids:
        kp_rows = (
            await session.execute(
                select(Film.kinopoisk_id, Film.title).where(Film.kinopoisk_id.in_(kp_ids)),
            )
        ).all()
        title_by_kp_id: dict[int, str] = {}
        for kp_id, title in kp_rows:
            if title is not None and str(title).strip() != '':
                title_by_kp_id[int(kp_id)] = str(title).strip()
        for key, min_kp_id in kp_id_by_key.items():
            title = title_by_kp_id.get(min_kp_id)
            if title is not None:
                labels[key] = title

    unresolved = [key for key in normalized if key not in labels]
    if unresolved:
        franchise_rows = (
            await session.execute(
                select(
                    Film.franchise_key,
                    Film.title,
                    Film.tmdb_detail_snapshot_json,
                    Film.kinopoisk_id,
                    Film.id,
                )
                .where(Film.franchise_key.in_(unresolved))
                .order_by(
                    Film.franchise_key,
                    Film.kinopoisk_id.asc().nulls_last(),
                    Film.id.asc(),
                ),
            )
        ).all()
        films_by_key: dict[str, list[tuple[object, object, int | None, int]]] = {}
        for franchise_key, title, snapshot, kp_id, film_id in franchise_rows:
            fk = str(franchise_key)
            films_by_key.setdefault(fk, []).append((title, snapshot, kp_id, film_id))

        for key in unresolved:
            films = films_by_key.get(key, [])

            if parse_franchise_tmdb_collection_id(key) is not None:
                for _, snapshot, _, _ in films:
                    collection_name = collection_name_from_snapshot(snapshot)
                    if collection_name is not None:
                        labels[key] = collection_name
                        break

            if key not in labels and films:
                first_title = films[0][0]
                if first_title is not None and str(first_title).strip() != '':
                    labels[key] = str(first_title).strip()

            if key not in labels:
                labels[key] = franchise_fallback_label(key)

    return labels


async def resolve_franchise_label(session: AsyncSession, franchise_key: str) -> str:
    key = franchise_key.strip()
    if key == '':
        return franchise_fallback_label(key)
    labels = await resolve_franchise_labels(session, [key])
    return labels.get(key, franchise_fallback_label(key))
