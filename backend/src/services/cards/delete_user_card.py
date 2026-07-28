from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard


class UserCardNotFoundError(Exception):
    pass


class UserCardForbiddenError(Exception):
    pass


class DeleteUserCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, card_id: int, viewer_user_id: UUID) -> None:
        card = (
            await self._session.execute(select(UserCard).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise UserCardNotFoundError
        if card.user_id != viewer_user_id:
            raise UserCardForbiddenError
        await self._session.delete(card)
        await self._session.commit()
