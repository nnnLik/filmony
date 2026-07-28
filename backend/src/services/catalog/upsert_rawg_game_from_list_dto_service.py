from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.game import Game
from providers.rawg.rawg_openapi_dto import RawgGameDTO

from .rawg_game_snapshot_utils import merge_list_dto_into_game, utc_now


@dataclass
class UpsertRawgGameFromListDtoService:
    """Upserts RAWG ``Game`` fields available from search/list payloads.

    Leaves detail-only columns intact when merging into an existing row.
    """

    _session: AsyncSession

    class MissingRawgIdentifierError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, dto: RawgGameDTO) -> Game:
        if dto.id is None:
            raise self.MissingRawgIdentifierError('RAWG list item is missing numeric id')

        now = utc_now()
        stmt = select(Game).where(Game.rawg_id == dto.id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = Game(rawg_id=dto.id)
            self._session.add(row)
        merge_list_dto_into_game(row, dto, synced_at=now)
        await self._session.flush()
        return row


__all__ = ('UpsertRawgGameFromListDtoService',)
