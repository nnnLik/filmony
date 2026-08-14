from __future__ import annotations

from typing import Any

_PROVIDER_BUCKETS = ('flatrate', 'rent', 'buy')


def extract_ru_watch_provider_names(snapshot: Any | None) -> list[str]:
    if not isinstance(snapshot, dict):
        return []
    watch_providers = snapshot.get('watch/providers')
    if not isinstance(watch_providers, dict):
        return []
    results = watch_providers.get('results')
    if not isinstance(results, dict):
        return []
    ru_providers = results.get('RU')
    if not isinstance(ru_providers, dict):
        return []

    names: list[str] = []
    seen: set[str] = set()
    for bucket in _PROVIDER_BUCKETS:
        entries = ru_providers.get(bucket)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            provider_name = entry.get('provider_name')
            if not isinstance(provider_name, str):
                continue
            normalized = provider_name.strip()
            if normalized == '' or normalized in seen:
                continue
            seen.add(normalized)
            names.append(normalized)
    return names


__all__ = ('extract_ru_watch_provider_names',)
