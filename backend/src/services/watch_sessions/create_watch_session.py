from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.watch_session import WatchSession
from models.watch_session_enums import WatchSessionStatus


def _participant_ids_json(*, initiator_user_id: UUID, partner_user_ids: list[UUID]) -> list[str]:
    seen: set[UUID] = {initiator_user_id}
    ordered: list[UUID] = [initiator_user_id]
    for partner_id in partner_user_ids:
        if partner_id in seen:
            continue
        seen.add(partner_id)
        ordered.append(partner_id)
    return [str(uid) for uid in ordered]


@dataclass
class CreateWatchSessionService:
    """Creates a planned co-view session when a watch-with watchlist invite is sent."""

    _session: AsyncSession

    class InvalidAnchorError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        initiator_user_id: UUID,
        partner_user_ids: list[UUID],
        anchor_film_id: int | None,
        anchor_catalog_item_id: int | None,
        source_watchlist_entry_id: int | None,
        source_watch_party_id: UUID | None = None,
    ) -> WatchSession:
        has_film = anchor_film_id is not None
        has_catalog = anchor_catalog_item_id is not None
        if has_film == has_catalog:
            raise self.InvalidAnchorError

        entity = WatchSession(
            initiator_user_id=initiator_user_id,
            anchor_film_id=anchor_film_id,
            anchor_catalog_item_id=anchor_catalog_item_id,
            participant_user_ids=_participant_ids_json(
                initiator_user_id=initiator_user_id,
                partner_user_ids=partner_user_ids,
            ),
            status=WatchSessionStatus.planned,
            source_watchlist_entry_id=source_watchlist_entry_id,
            source_watch_party_id=source_watch_party_id,
        )
        self._session.add(entity)
        await self._session.flush()
        return entity
