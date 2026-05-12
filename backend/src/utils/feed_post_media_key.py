from __future__ import annotations


def is_safe_feed_post_media_key(key: str) -> bool:
    """Allow only RustFS keys under approved user-media prefixes (no traversal)."""
    k = key.strip().lstrip('/')
    if k == '' or '..' in k:
        return False
    return k.startswith('user_media/feed_posts/') or k.startswith('user_media/movie_card_comments/')
