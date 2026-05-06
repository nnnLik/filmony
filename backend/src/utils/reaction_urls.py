from __future__ import annotations

from conf import settings


def resolve_reaction_media_url(
    *, asset_key: str | None, image_url_fallback: str, public_base: str
) -> str:
    key_raw = asset_key.strip() if asset_key else ''
    internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
    if internal and key_raw:
        safe_key = key_raw.lstrip('/')
        return f'/api/reactions/asset/{safe_key}'
    base = public_base.strip().rstrip('/')
    if base and key_raw:
        return f'{base}/{key_raw.lstrip("/")}'
    return image_url_fallback
