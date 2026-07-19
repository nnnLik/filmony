from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from services.feed_posts.upload_feed_post_image import (
    FeedPostImageUploadError,
    UploadFeedPostImageService,
)
from utils.user_card_media_key import USER_CARD_MEDIA_API_PATH_PREFIX

__all__ = ['FeedPostImageUploadError', 'UploadUserCardCoverService']


@dataclass
class UploadUserCardCoverService:
    """Upload a user card cover image to RustFS and return the cards media proxy path."""

    _upload_feed_post_image: UploadFeedPostImageService

    @classmethod
    def build(cls) -> Self:
        return cls(_upload_feed_post_image=UploadFeedPostImageService.build())

    async def execute(
        self,
        *,
        user_id: UUID,
        content_type: str,
        data: bytes,
    ) -> str:
        feed_post_url = await self._upload_feed_post_image.execute(
            user_id=user_id,
            content_type=content_type,
            data=data,
            media_subdir='user_card_covers',
        )
        key = feed_post_url.removeprefix('/api/feed-posts/media/').lstrip('/')
        return f'{USER_CARD_MEDIA_API_PATH_PREFIX}{key}'
