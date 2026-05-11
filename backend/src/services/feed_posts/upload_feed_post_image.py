from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from conf import settings
from utils.rustfs_put_object import RustfsPutObjectError, put_rustfs_object_bytes

_ALLOWED_CT_SUFFIX: dict[str, str] = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/gif': '.gif',
}

FEED_POST_IMAGE_MAX_BYTES = 5 * 1024 * 1024


class FeedPostImageUploadError(Exception):
    """Invalid type/size or storage not configured."""


@dataclass
class UploadFeedPostImageService:
    """Writes one validated image for a feed post to RustFS and returns the API proxy path.

    The returned path is stored in ``FeedPost.image_url``; clients load pixels via
    ``GET /api/feed-posts/media/…`` without a Bearer header on the image request.
    """

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(self, *, user_id: UUID, content_type: str, data: bytes) -> str:
        ct = content_type.strip().lower()
        if ct not in _ALLOWED_CT_SUFFIX:
            raise FeedPostImageUploadError('unsupported image type')
        if len(data) == 0:
            raise FeedPostImageUploadError('empty file')
        if len(data) > FEED_POST_IMAGE_MAX_BYTES:
            raise FeedPostImageUploadError('file too large')

        internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
        if not internal:
            raise FeedPostImageUploadError('storage not configured')

        bucket = settings.reaction_media.rustfs_bucket.strip()
        access = settings.reaction_media.rustfs_access_key.strip()
        secret = settings.reaction_media.rustfs_secret_key.strip()
        if not bucket or not access or not secret:
            raise FeedPostImageUploadError('storage not configured')

        ext = _ALLOWED_CT_SUFFIX[ct]
        key = f'user_media/feed_posts/{user_id}/{uuid4().hex}{ext}'

        try:
            await asyncio.to_thread(
                put_rustfs_object_bytes,
                endpoint_url=internal,
                access_key_id=access,
                secret_access_key=secret,
                bucket=bucket,
                key=key,
                body=data,
                content_type=ct,
            )
        except RustfsPutObjectError as exc:
            raise FeedPostImageUploadError(str(exc)) from exc

        return f'/api/feed-posts/media/{key}'
