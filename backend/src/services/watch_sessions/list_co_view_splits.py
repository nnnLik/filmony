from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_card import UserCard
from models.watch_session import WatchSession


@dataclass(frozen=True, slots=True)
class CoViewSplit:
    user_id: UUID
    profile_slug: str
    rating: float


def _parse_participant_ids(raw: list) -> list[UUID]:
    out: list[UUID] = []
    for item in raw or []:
        try:
            out.append(UUID(str(item)))
        except (TypeError, ValueError):
            continue
    return out


@dataclass
class ListCoViewSplitsService:
    """Returns rated participant splits for a finalized co-view session."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, watch_session_id: UUID) -> tuple[CoViewSplit, ...]:
        session = await self._session.get(WatchSession, watch_session_id)
        if session is None:
            return ()

        participant_ids = _parse_participant_ids(session.participant_user_ids)
        if not participant_ids:
            return ()

        users_by_id: dict[UUID, User] = {}
        for user in (
            await self._session.execute(select(User).where(User.id.in_(participant_ids)))
        ).scalars():
            users_by_id[user.id] = user

        splits: list[CoViewSplit] = []
        for participant_id in participant_ids:
            card = await self._rated_card_for_participant(
                participant_id,
                anchor_film_id=session.anchor_film_id,
                anchor_catalog_item_id=session.anchor_catalog_item_id,
            )
            if card is None:
                continue
            user = users_by_id.get(participant_id)
            slug = (user.profile_slug if user is not None else '') or str(participant_id)
            splits.append(
                CoViewSplit(
                    user_id=participant_id,
                    profile_slug=slug,
                    rating=float(card.rating),
                )
            )
        return tuple(splits)

    async def _rated_card_for_participant(
        self,
        user_id: UUID,
        *,
        anchor_film_id: int | None,
        anchor_catalog_item_id: int | None,
    ) -> UserCard | None:
        stmt = select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.is_planned.is_(False),
        )
        if anchor_film_id is not None:
            stmt = stmt.where(UserCard.film_id == anchor_film_id)
        elif anchor_catalog_item_id is not None:
            stmt = stmt.where(UserCard.catalog_item_id == anchor_catalog_item_id)
        else:
            return None
        stmt = stmt.order_by(UserCard.completed_at.desc(), UserCard.id.desc()).limit(1)
        return (await self._session.execute(stmt)).scalar_one_or_none()
