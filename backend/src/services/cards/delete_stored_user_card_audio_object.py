from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self

from core.rustfs_s3_client import RustfsDeleteObjectError, RustfsS3Client
from utils.user_card_media_key import rustfs_key_from_user_card_audio_proxy_url


@dataclass
class DeleteStoredUserCardAudioObjectService:
    """Deletes the RustFS object behind a stored card audio proxy URL (best-effort).

    Used after replacing or removing card audio so orphaned objects do not linger in the bucket.
    Missing configuration or delete errors are ignored so user flows are not blocked.
    """

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(self, *, old_proxy_url: str | None) -> None:
        key = rustfs_key_from_user_card_audio_proxy_url(old_proxy_url)
        if key is None:
            return
        client = RustfsS3Client.try_build_from_settings()
        if client is None:
            return
        try:
            await asyncio.to_thread(client.delete_object, key)
        except RustfsDeleteObjectError:
            return
