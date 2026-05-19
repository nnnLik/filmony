from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.user_card import UserCard


@dataclass(frozen=True, slots=True)
class UserCardTagStat:
    """Single custom tag aggregated across the user's movie cards."""

    tag: str
    use_count: int


class ListMyUserCardTagStatsService:
    """Returns the viewer's custom tags with usage counts for autocomplete UIs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, *, limit: int) -> list[UserCardTagStat]:
        cnt = func.count(CardTag.card_id)
        stmt = (
            select(CardTag.tag, cnt)
            .join(UserCard, UserCard.id == CardTag.card_id)
            .where(UserCard.user_id == user_id)
            .group_by(CardTag.tag)
            .order_by(cnt.desc(), CardTag.tag.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [UserCardTagStat(tag=str(t), use_count=int(c)) for t, c in rows]
