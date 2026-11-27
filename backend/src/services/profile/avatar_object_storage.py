"""Put and delete the single RustFS object used as a user's custom avatar."""

from __future__ import annotations

import asyncio
from uuid import UUID

from core.rustfs_s3_client import (
    RustfsDeleteObjectError,
    RustfsPutObjectError,
    RustfsS3Client,
)
from utils.avatar_photo_url import avatar_object_key


class AvatarObjectStorageError(Exception):
    """RustFS is missing or the avatar object could not be written or removed."""


def _client() -> RustfsS3Client:
    client = RustfsS3Client.try_build_from_settings()
    if client is None:
        raise AvatarObjectStorageError('storage not configured')
    return client


async def delete_avatar_object(user_id: UUID) -> None:
    client = _client()
    try:
        await asyncio.to_thread(client.delete_object, avatar_object_key(user_id))
    except RustfsDeleteObjectError as exc:
        raise AvatarObjectStorageError('storage unreachable') from exc


async def put_avatar_object(user_id: UUID, data: bytes, content_type: str) -> None:
    client = _client()
    try:
        await asyncio.to_thread(
            client.put_object,
            avatar_object_key(user_id),
            data,
            content_type,
        )
    except RustfsPutObjectError as exc:
        raise AvatarObjectStorageError('storage unreachable') from exc
