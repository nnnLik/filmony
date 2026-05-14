from __future__ import annotations

from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard


class GetMyMovieCardIdForFilmService:
    """Looks up the viewer's rated card for a catalog film, if any."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session)

    async def execute(self, user_id: UUID, film_id: int) -> int | None:
        q = await self._session.execute(
            select(UserCard.id).where(UserCard.user_id == user_id, UserCard.film_id == film_id)
        )
        return q.scalar_one_or_none()

    async def execute_many(self, user_id: UUID, film_ids: list[int]) -> dict[int, int]:
        """film_id -> movie_card_id for the viewer's rated cards."""
        if not film_ids:
            return {}
        q = await self._session.execute(
            select(UserCard.film_id, UserCard.id).where(
                UserCard.user_id == user_id,
                UserCard.film_id.in_(film_ids),
            )
        )
        return {int(fid): int(cid) for fid, cid in q.all()}
