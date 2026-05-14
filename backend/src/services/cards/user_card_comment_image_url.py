from __future__ import annotations

from utils.feed_post_media_key import is_safe_feed_post_media_key

_MEDIA_PREFIX = '/api/feed-posts/media/'


def normalize_user_card_comment_image_url(raw: str | None) -> str | None:
    """Strip and validate stored image path for a movie-card comment (same proxy as feed posts)."""
    if raw is None:
        return None
    s = raw.strip()
    if s == '':
        return None
    if len(s) > 2048:
        raise ValueError('image_url max length is 2048')
    if not s.startswith(_MEDIA_PREFIX):
        raise ValueError('invalid image_url')
    key = s[len(_MEDIA_PREFIX) :].lstrip('/')
    if not is_safe_feed_post_media_key(key):
        raise ValueError('invalid image_url')
    return s
