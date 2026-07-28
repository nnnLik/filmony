from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reaction_target_kind import ReactionTargetKind
from models.user import User
from models.user_reaction import UserReaction


@dataclass(frozen=True, slots=True)
class ReactionActorRow:
    id: UUID
    profile_slug: str
    display_name: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None


class ListReactionActorsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        *,
        target_kind: ReactionTargetKind,
        target_id: int,
        reaction_type_id: int,
        limit: int = 50,
    ) -> tuple[ReactionActorRow, ...]:
        cap = min(max(limit, 1), 50)
        stmt = (
            select(
                User.id,
                User.profile_slug,
                User.display_name,
                User.username,
                User.first_name,
                User.last_name,
                User.photo_url,
            )
            .join(UserReaction, UserReaction.user_id == User.id)
            .where(
                UserReaction.target_kind == target_kind.value,
                UserReaction.target_id == target_id,
                UserReaction.reaction_type_id == reaction_type_id,
            )
            .order_by(UserReaction.id.desc())
            .limit(cap)
        )
        rows = (await self._session.execute(stmt)).all()
        return tuple(
            ReactionActorRow(
                id=r[0],
                profile_slug=str(r[1]),
                display_name=r[2],
                username=r[3],
                first_name=r[4],
                last_name=r[5],
                photo_url=r[6],
            )
            for r in rows
        )
