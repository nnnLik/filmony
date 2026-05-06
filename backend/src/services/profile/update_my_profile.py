from __future__ import annotations

from re import fullmatch
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

_PROFILE_SLUG_PATTERN = r'^[a-z0-9][a-z0-9-]{1,30}$'


class ProfileSlugInvalidError(Exception):
    pass


class ProfileSlugTakenError(Exception):
    pass


class UpdateMyProfileService:
    """Apply allowed profile field updates for the current user.

    Pass only keys present in the JSON body (PATCH semantics). Supported keys:
    ``display_name``, ``bio``, ``profile_slug`` (each may be ``null`` to clear text fields).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, patch: dict[str, Any]) -> User:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            msg = 'user not found'
            raise ValueError(msg)

        if 'display_name' in patch:
            raw = patch['display_name']
            if raw is None:
                user.display_name = None
            elif isinstance(raw, str):
                user.display_name = raw.strip() or None
            else:
                msg = 'display_name must be string or null'
                raise ValueError(msg)

        if 'bio' in patch:
            raw = patch['bio']
            if raw is None:
                user.bio = None
            elif isinstance(raw, str):
                user.bio = raw.strip() or None
            else:
                msg = 'bio must be string or null'
                raise ValueError(msg)

        if 'profile_slug' in patch:
            raw = patch['profile_slug']
            if raw is None:
                msg = 'profile_slug cannot be null'
                raise ValueError(msg)
            if not isinstance(raw, str):
                msg = 'profile_slug must be a string'
                raise ValueError(msg)
            new_slug = raw.strip().lower()
            if fullmatch(_PROFILE_SLUG_PATTERN, new_slug) is None:
                raise ProfileSlugInvalidError
            if new_slug != user.profile_slug:
                taken = await self._session.execute(
                    select(User.id).where(User.profile_slug == new_slug, User.id != user_id)
                )
                if taken.scalar_one_or_none() is not None:
                    raise ProfileSlugTakenError
                user.profile_slug = new_slug

        await self._session.commit()
        await self._session.refresh(user)
        return user
