"""Franchise label helpers."""

from __future__ import annotations

import re

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


async def resolve_franchise_label(session: AsyncSession, franchise_key: str) -> str:
    key = franchise_key.strip()
    if key == '':
        return franchise_fallback_label(key)

    min_kp_id = parse_franchise_min_kinopoisk_id(key)
    if min_kp_id is not None:
        title_row = (
            await session.execute(
                select(Film.title).where(Film.kinopoisk_id == min_kp_id).limit(1),
            )
        ).scalar_one_or_none()
        if title_row is not None and str(title_row).strip() != '':
            return str(title_row).strip()

    collection_id = parse_franchise_tmdb_collection_id(key)
    if collection_id is not None:
        snapshot_rows = (
            await session.execute(
                select(Film.tmdb_detail_snapshot_json).where(Film.franchise_key == key).limit(1),
            )
        ).scalar_one_or_none()
        collection_name = collection_name_from_snapshot(snapshot_rows)
        if collection_name is not None:
            return collection_name

    return franchise_fallback_label(key)
