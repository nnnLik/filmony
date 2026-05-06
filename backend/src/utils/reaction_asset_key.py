from __future__ import annotations

from const.reaction_packs import REACTION_TAB_ORDER

_ALLOWED_SUFFIX = frozenset({'png', 'gif', 'webp', 'jpg', 'jpeg'})
_SLUGS = frozenset(tab.slug for tab in REACTION_TAB_ORDER)


def is_safe_reaction_asset_key(key: str) -> bool:
    k = key.strip().lstrip('/')
    parts = k.split('/')
    if len(parts) != 3:
        return False
    root, slug, fname = parts
    if root != 'reactions':
        return False
    if slug not in _SLUGS:
        return False
    if not fname or '..' in fname or '/' in fname or '\\' in fname:
        return False
    if '.' not in fname:
        return False
    ext = fname.rsplit('.', 1)[-1].lower()
    return ext in _ALLOWED_SUFFIX
