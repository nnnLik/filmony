"""Сборка публичного URL ассета реакции."""

from __future__ import annotations


def resolve_reaction_media_url(
    *, asset_key: str | None, image_url_fallback: str, public_base: str
) -> str:
    base = public_base.strip().rstrip('/')
    key = asset_key.strip() if asset_key else ''
    if base and key:
        return f'{base}/{key.lstrip("/")}'
    return image_url_fallback
