from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_recent_reaction import UserRecentReaction


class TouchUserRecentReactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, *, user_id: UUID, reaction_type_id: int) -> None:
        stmt = insert(UserRecentReaction).values(
            user_id=user_id,
            reaction_type_id=reaction_type_id,
            last_used_at=func.now(),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'reaction_type_id'],
            set_={'last_used_at': func.now()},
        )
        await self._session.execute(stmt)
