from __future__ import annotations

USER_CARD_AUDIO_RUSTFS_KEY_PREFIX = 'user_media/movie_card_audio/'
USER_CARD_MEDIA_API_PATH_PREFIX = '/api/cards/media/'


def is_safe_user_card_media_key(key: str) -> bool:
    """Allow only RustFS keys under approved user-card audio prefix (no traversal)."""
    k = key.strip().lstrip('/')
    if k == '' or '..' in k:
        return False
    return k.startswith(USER_CARD_AUDIO_RUSTFS_KEY_PREFIX)


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
