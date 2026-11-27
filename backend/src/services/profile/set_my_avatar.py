"""Replace the signed-in user's displayed avatar with an uploaded image."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.profile.avatar_object_storage import (
    AvatarObjectStorageError,
    delete_avatar_object,
    put_avatar_object,
)
from services.profile.resolve_telegram_avatar_url import ResolveTelegramAvatarUrlService
from utils.avatar_photo_url import (
    ALLOWED_AVATAR_CONTENT_TYPES,
    AVATAR_MAX_BYTES,
    custom_avatar_photo_url,
    declared_image_content_type,
    is_custom_avatar_photo_url,
    sniff_image_content_type,
)


@dataclass
class SetMyAvatarService:
    """Stores one image in RustFS and points ``photo_url`` at the public media path.

    Replacing a custom avatar deletes the previous object first. If the new upload
    fails after that delete, ``photo_url`` is set back to the Telegram avatar so the
    profile does not keep a broken media URL. An empty file is rejected.
    """

    _session: AsyncSession
    _resolve_telegram_avatar: ResolveTelegramAvatarUrlService

    class AvatarValidationError(Exception):
        pass

    class AvatarStorageError(Exception):
        pass

    class UserNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _resolve_telegram_avatar=ResolveTelegramAvatarUrlService.build(),
        )

    async def execute(self, user_id: UUID, content_type: str, data: bytes) -> User:
        image_type = self._validated_content_type(content_type, data)
        user = await self._load_user(user_id)
        was_custom = is_custom_avatar_photo_url(user.photo_url)
        if was_custom:
            try:
                await delete_avatar_object(user_id)
            except AvatarObjectStorageError as exc:
                raise self.AvatarStorageError(str(exc)) from exc
        try:
            await put_avatar_object(user_id, data, image_type)
        except AvatarObjectStorageError as exc:
            if was_custom:
                await self._restore_telegram_photo(user)
            raise self.AvatarStorageError(str(exc)) from exc

        user.photo_url = custom_avatar_photo_url(user_id, time.time_ns())
        await self._session.commit()
        await self._session.refresh(user)
        return user

    def _validated_content_type(self, content_type: str, data: bytes) -> str:
        if len(data) == 0:
            raise self.AvatarValidationError('empty file')
        if len(data) > AVATAR_MAX_BYTES:
            raise self.AvatarValidationError('file too large')
        declared = declared_image_content_type(content_type)
        sniffed = sniff_image_content_type(data)
        if declared not in ALLOWED_AVATAR_CONTENT_TYPES or sniffed != declared:
            raise self.AvatarValidationError('unsupported image type')
        return declared

    async def _load_user(self, user_id: UUID) -> User:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise self.UserNotFound
        return user

    async def _restore_telegram_photo(self, user: User) -> None:
        user.photo_url = await self._resolve_telegram_avatar.execute(
            user_id=user.id,
            telegram_user_id=user.telegram_user_id,
            username=user.username,
        )
        if user.photo_url == '':
            user.photo_url = None
        await self._session.commit()
        await self._session.refresh(user)
