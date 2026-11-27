"""Remove the signed-in user's custom avatar and show the Telegram photo again."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.profile.avatar_object_storage import AvatarObjectStorageError, delete_avatar_object
from services.profile.resolve_telegram_avatar_url import ResolveTelegramAvatarUrlService
from utils.avatar_photo_url import is_custom_avatar_photo_url


@dataclass
class ClearMyAvatarService:
    """Deletes the custom avatar object and writes the Telegram photo URL back.

    When the displayed photo is already the Telegram one, the profile is returned
    unchanged. The stored URL is never an empty string: Telegram's own photo, or
    null when Telegram has no photo (initials in the UI).
    """

    _session: AsyncSession
    _resolve_telegram_avatar: ResolveTelegramAvatarUrlService

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

    async def execute(self, user_id: UUID) -> User:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise self.UserNotFound
        if not is_custom_avatar_photo_url(user.photo_url):
            return user

        try:
            await delete_avatar_object(user_id)
        except AvatarObjectStorageError as exc:
            raise self.AvatarStorageError(str(exc)) from exc

        restored = await self._resolve_telegram_avatar.execute(
            user_id=user.id,
            telegram_user_id=user.telegram_user_id,
            username=user.username,
        )
        user.photo_url = None if restored == '' else restored
        await self._session.commit()
        await self._session.refresh(user)
        return user
