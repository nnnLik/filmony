from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from services.cards.delete_stored_user_card_audio_object import (
    DeleteStoredUserCardAudioObjectService,
)


class UserCardNotFoundError(Exception):
    pass


class UserCardForbiddenError(Exception):
    pass


@dataclass
class DeleteUserCardAudioService:
    """Removes stored card audio from RustFS and clears DB fields for the card."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session)

    async def execute(self, *, card_id: int, viewer_user_id: UUID) -> None:
        card = (
            await self._session.execute(select(UserCard).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise UserCardNotFoundError
        if card.user_id != viewer_user_id:
            raise UserCardForbiddenError

        old_url = card.audio_url
        card.audio_url = None
        await self._session.commit()
        await DeleteStoredUserCardAudioObjectService.build().execute(old_proxy_url=old_url)
