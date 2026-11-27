"""Read a custom avatar object for the public media route."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self

from core.rustfs_s3_client import (
    RustfsClientError,
    RustfsGetObjectResult,
    RustfsKeyNotFoundError,
    RustfsS3Client,
)
from utils.avatar_photo_url import is_safe_avatar_media_key


@dataclass
class GetAvatarMediaService:
    """Loads avatar bytes from RustFS when the key is a user avatar object."""

    class NotFound(Exception):
        pass

    class NotConfigured(Exception):
        pass

    class Unreachable(Exception):
        pass

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(self, media_key: str) -> RustfsGetObjectResult:
        if not is_safe_avatar_media_key(media_key):
            raise self.NotFound
        client = RustfsS3Client.try_build_from_settings()
        if client is None:
            raise self.NotConfigured
        try:
            return await asyncio.to_thread(client.get_object, media_key.lstrip('/'))
        except RustfsKeyNotFoundError as exc:
            raise self.NotFound from exc
        except RustfsClientError as exc:
            raise self.Unreachable from exc
