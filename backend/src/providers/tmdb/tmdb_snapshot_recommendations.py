from __future__ import annotations

from typing import Any


def extract_tmdb_recommendation_titles(
    snapshot: Any | None,
    *,
    limit: int = 6,
) -> list[str]:
    if not isinstance(snapshot, dict):
        return []
    recommendations = snapshot.get('recommendations')
    if not isinstance(recommendations, dict):
        return []
    results = recommendations.get('results')
    if not isinstance(results, list):
        return []
    titles: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get('title')
        if not isinstance(title, str):
            continue
        normalized = title.strip()
        if normalized == '':
            continue
        titles.append(normalized)
        if len(titles) >= limit:
            break
    return titles


__all__ = ('extract_tmdb_recommendation_titles',)
