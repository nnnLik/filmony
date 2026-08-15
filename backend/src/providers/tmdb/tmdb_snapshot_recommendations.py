from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TmdbRecommendationEntry:
    title: str
    tmdb_id: int | None


def _parse_tmdb_id(raw: object) -> int | None:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def extract_tmdb_recommendation_entries(
    snapshot: Any | None,
    *,
    limit: int = 6,
) -> list[TmdbRecommendationEntry]:
    if not isinstance(snapshot, dict):
        return []
    recommendations = snapshot.get('recommendations')
    if not isinstance(recommendations, dict):
        return []
    results = recommendations.get('results')
    if not isinstance(results, list):
        return []
    entries: list[TmdbRecommendationEntry] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get('title')
        if not isinstance(title, str):
            continue
        normalized = title.strip()
        if normalized == '':
            continue
        entries.append(
            TmdbRecommendationEntry(
                title=normalized,
                tmdb_id=_parse_tmdb_id(item.get('id')),
            ),
        )
        if len(entries) >= limit:
            break
    return entries


def extract_tmdb_recommendation_titles(
    snapshot: Any | None,
    *,
    limit: int = 6,
) -> list[str]:
    return [entry.title for entry in extract_tmdb_recommendation_entries(snapshot, limit=limit)]


__all__ = (
    'TmdbRecommendationEntry',
    'extract_tmdb_recommendation_entries',
    'extract_tmdb_recommendation_titles',
)
