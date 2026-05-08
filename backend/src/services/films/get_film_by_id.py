from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film


class GetFilmByIdService:
    """Loads a persisted Film row by primary key."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, film_id: int) -> Film | None:
        return (
            await self._session.execute(select(Film).where(Film.id == film_id))
        ).scalar_one_or_none()
