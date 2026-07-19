from __future__ import annotations

USER_CARD_AUDIO_RUSTFS_KEY_PREFIX = 'user_media/movie_card_audio/'
USER_CARD_COVER_RUSTFS_KEY_PREFIX = 'user_media/user_card_covers/'
USER_CARD_MEDIA_API_PATH_PREFIX = '/api/cards/media/'

_SAFE_USER_CARD_MEDIA_PREFIXES = (
    USER_CARD_AUDIO_RUSTFS_KEY_PREFIX,
    USER_CARD_COVER_RUSTFS_KEY_PREFIX,
)


def is_safe_user_card_media_key(key: str) -> bool:
    """Allow only RustFS keys under approved user-card media prefixes (no traversal)."""
    k = key.strip().lstrip('/')
    if k == '' or '..' in k:
        return False
    return any(k.startswith(prefix) for prefix in _SAFE_USER_CARD_MEDIA_PREFIXES)


def rustfs_key_from_user_card_audio_proxy_url(url: str | None) -> str | None:
    """Extract RustFS object key from stored ``/api/cards/media/...`` path."""
    if url is None:
        return None
    s = str(url).strip()
    if not s.startswith(USER_CARD_MEDIA_API_PATH_PREFIX):
        return None
    key = s.removeprefix(USER_CARD_MEDIA_API_PATH_PREFIX).lstrip('/')
    if not is_safe_user_card_media_key(key):
        return None
    return key
