from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from core.rustfs_s3_client import RustfsPutObjectError, RustfsS3Client

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

    async def execute(
        self,
        *,
        user_id: UUID,
        content_type: str,
        data: bytes,
        media_subdir: str = 'feed_posts',
    ) -> str:
        ct = content_type.strip().lower()
        if ct not in _ALLOWED_CT_SUFFIX:
            raise FeedPostImageUploadError('unsupported image type')
        if len(data) == 0:
            raise FeedPostImageUploadError('empty file')
        if len(data) > FEED_POST_IMAGE_MAX_BYTES:
            raise FeedPostImageUploadError('file too large')

        client = RustfsS3Client.try_build_from_settings()
        if client is None:
            raise FeedPostImageUploadError('storage not configured')

        if media_subdir not in ('feed_posts', 'movie_card_comments'):
            raise FeedPostImageUploadError('invalid media path')
        ext = _ALLOWED_CT_SUFFIX[ct]
        key = f'user_media/{media_subdir}/{user_id}/{uuid4().hex}{ext}'

        try:
            await asyncio.to_thread(client.put_object, key, data, ct)
        except RustfsPutObjectError as exc:
            raise FeedPostImageUploadError(str(exc)) from exc

        return f'/api/feed-posts/media/{key}'
