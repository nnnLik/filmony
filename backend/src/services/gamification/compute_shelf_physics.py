from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard

ShelfPhysicsMode = Literal['neutral', 'slump', 'glow']


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


@dataclass(frozen=True, slots=True)
class ShelfPhysicsDTO:
    mode: ShelfPhysicsMode
    streak_length: int


@dataclass
class ComputeShelfPhysicsService:
    """Derives shelf visual mode from the user's most recent rated cards."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> ShelfPhysicsDTO:
        ratings = (
            (
                await self._session.execute(
                    select(UserCard.rating)
                    .where(
                        UserCard.user_id == user_id,
                        UserCard.is_planned.is_(False),
                        UserCard.rating >= 1,
                    )
                    .order_by(desc(_completion_timestamp()), desc(UserCard.id))
                    .limit(5),
                )
            )
            .scalars()
            .all()
        )

        rating_values = [float(rating) for rating in ratings]

        low_streak = 0
        for rating in rating_values:
            if rating <= 3:
                low_streak += 1
            else:
                break

        high_streak = 0
        for rating in rating_values:
            if rating >= 9:
                high_streak += 1
            else:
                break

        if low_streak >= 3:
            return ShelfPhysicsDTO(mode='slump', streak_length=low_streak)
        if high_streak >= 3:
            return ShelfPhysicsDTO(mode='glow', streak_length=high_streak)
        return ShelfPhysicsDTO(mode='neutral', streak_length=0)
