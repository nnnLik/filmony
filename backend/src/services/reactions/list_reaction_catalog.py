from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reaction_type import ReactionType


@dataclass(frozen=True, slots=True)
class ReactionCatalogItem:
    id: int
    label: str | None
    image_url: str


class ListReactionCatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self) -> tuple[ReactionCatalogItem, ...]:
        rows = (
            (
                await self._session.execute(
                    select(ReactionType)
                    .where(ReactionType.is_active.is_(True))
                    .order_by(ReactionType.sort_order.asc(), ReactionType.id.asc())
                )
            )
            .scalars()
            .all()
        )
        return tuple(
            ReactionCatalogItem(id=r.id, label=r.label, image_url=r.image_url) for r in rows
        )
