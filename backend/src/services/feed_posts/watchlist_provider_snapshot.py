from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WatchlistProviderSnapshot:
    title: str
    description: str | None
    poster_url: str | None


def build_watchlist_provider_snapshot(provider_meta: dict) -> WatchlistProviderSnapshot:
    provider = str(provider_meta.get('provider') or '').strip()
    data = provider_meta.get('data') or {}
    if not isinstance(data, dict):
        data = {}

    title = 'Untitled'
    description: str | None = None
    poster_url: str | None = None

    if provider == 'kinopoisk':
        kp_id = data.get('kp_id')
        title = str(data.get('title') or (f'Kinopoisk #{kp_id}' if kp_id is not None else 'Film'))
        description = _optional_str(data.get('description'))
        poster_url = _optional_str(data.get('poster_url') or data.get('display_cover_url'))
    elif provider == 'rawg':
        slug = data.get('slug') or data.get('external_id')
        title = str(data.get('title') or slug or 'Game')
        description = _optional_str(data.get('description'))
        poster_url = _optional_str(data.get('poster_url') or data.get('display_cover_url'))
    elif provider == 'custom':
        title = str(data.get('title') or data.get('display_title') or 'Custom card')
        description = _optional_str(data.get('description'))
        poster_url = _optional_str(data.get('poster_url') or data.get('display_cover_url'))
    else:
        title = str(data.get('title') or provider or 'Watchlist item')
        description = _optional_str(data.get('description'))
        poster_url = _optional_str(data.get('poster_url') or data.get('display_cover_url'))

    return WatchlistProviderSnapshot(
        title=title,
        description=description,
        poster_url=poster_url,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text != '' else None
