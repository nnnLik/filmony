from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.auth.dto import TelegramWebAppUser
from services.profile.allocate_default_profile_slug import AllocateDefaultProfileSlugService


class UpsertTelegramUserService:
    """Create or update a user row from verified Telegram Web App user data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, profile: TelegramWebAppUser) -> User:
        now = dt.datetime.now(dt.UTC)
        result = await self._session.execute(
            select(User).where(User.telegram_user_id == profile.telegram_user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            slug = await AllocateDefaultProfileSlugService(self._session).execute()
            user = User(
                telegram_user_id=profile.telegram_user_id,
                username=profile.username,
                first_name=profile.first_name,
                last_name=profile.last_name,
                photo_url=profile.photo_url,
                language_code=profile.language_code,
                profile_slug=slug,
            )
            self._session.add(user)
        else:
            user.username = profile.username
            user.first_name = profile.first_name
            user.last_name = profile.last_name
            user.photo_url = profile.photo_url
            user.language_code = profile.language_code
            user.updated_at = now
            if not user.profile_slug:
                user.profile_slug = await AllocateDefaultProfileSlugService(self._session).execute()

        await self._session.commit()
        await self._session.refresh(user)
        return user
