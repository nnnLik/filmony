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
from services.cards.upload_user_card_audio import UploadUserCardAudioService


class UserCardNotFoundError(Exception):
    pass


class UserCardForbiddenError(Exception):
    pass


@dataclass
class AttachUserCardAudioService:
    """Uploads audio for a user-owned card and persists the proxy URL (replacing any prior file)."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session)

    async def execute(
        self,
        *,
        card_id: int,
        viewer_user_id: UUID,
        content_type: str,
        data: bytes,
    ) -> UserCard:
        card = (
            await self._session.execute(select(UserCard).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise UserCardNotFoundError
        if card.user_id != viewer_user_id:
            raise UserCardForbiddenError

        old_url = card.audio_url
        proxy_url = await UploadUserCardAudioService.build().execute(
            user_id=viewer_user_id,
            content_type=content_type,
            data=data,
        )

        card.audio_url = proxy_url
        await self._session.commit()
        await self._session.refresh(card)
        await DeleteStoredUserCardAudioObjectService.build().execute(old_proxy_url=old_url)
        return card
