from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from services.collections.meaningful_rated_card import is_meaningful_rated_card
from services.collections.refresh_progress_for_film import RefreshProgressForFilmService


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
        should_refresh = is_meaningful_rated_card(card)
        film_id = card.film_id
        await self._session.delete(card)
        await self._session.commit()
        if should_refresh and film_id is not None:
            await RefreshProgressForFilmService.build(self._session).execute(
                viewer_user_id,
                film_id,
            )
