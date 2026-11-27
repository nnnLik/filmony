"""Custom avatar URLs live in ``User.photo_url``; the object key is derived from the user id."""

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID

AVATAR_MAX_BYTES = 5 * 1024 * 1024

ALLOWED_AVATAR_CONTENT_TYPES = frozenset(
    {'image/jpeg', 'image/png', 'image/webp', 'image/gif'},
)

_AVATAR_KEY_PREFIX = 'user_media/avatars/'
_CUSTOM_AVATAR_PATH_PREFIX = f'/api/users/avatar-media/{_AVATAR_KEY_PREFIX}'


def avatar_object_key(user_id: UUID) -> str:
    return f'{_AVATAR_KEY_PREFIX}{user_id}'


def custom_avatar_photo_url(user_id: UUID, version: int) -> str:
    return f'/api/users/avatar-media/{avatar_object_key(user_id)}?v={version}'


def telegram_userpic_url(username: str) -> str:
    return f'https://t.me/i/userpic/320/{quote(username.strip(), safe="")}.jpg'


def telegram_avatar_proxy_path(user_id: UUID) -> str:
    return f'/api/users/{user_id}/telegram-avatar'


def photo_url_path(photo_url: str) -> str:
    return photo_url.strip().split('?', 1)[0]


def is_custom_avatar_photo_url(photo_url: str | None) -> bool:
    if photo_url is None or photo_url.strip() == '':
        return False
    return photo_url_path(photo_url).startswith(_CUSTOM_AVATAR_PATH_PREFIX)


def is_safe_avatar_media_key(key: str) -> bool:
    """Allow only ``user_media/avatars/{uuid}`` with no traversal."""
    k = key.strip().lstrip('/')
    if k == '' or '..' in k or '\\' in k or '?' in k:
        return False
    if not k.startswith(_AVATAR_KEY_PREFIX):
        return False
    rest = k[len(_AVATAR_KEY_PREFIX) :]
    if rest == '' or '/' in rest:
        return False
    try:
        parsed = UUID(rest)
    except ValueError:
        return False
    return str(parsed) == rest


def sniff_image_content_type(body: bytes) -> str | None:
    """Detect an image type from its signature. Rejects HTML and other non-images."""
    if len(body) < 12:
        return None
    if body.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if body.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if body.startswith((b'GIF87a', b'GIF89a')):
        return 'image/gif'
    if body.startswith(b'RIFF') and body[8:12] == b'WEBP':
        return 'image/webp'
    return None


def declared_image_content_type(content_type: str) -> str:
    return content_type.split(';', 1)[0].strip().lower()
