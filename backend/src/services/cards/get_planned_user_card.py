from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_enums import CardCompany
from models.catalog_item import CatalogItem, CatalogProvider
from models.user_card import UserCard


@dataclass(frozen=True, slots=True)
class PlannedUserCardDTO:
    user_card_id: int
    company: CardCompany
    category_id: int
    watch_note: str


@dataclass
class GetPlannedUserCardService:
    """Returns planned card metadata for prefill when rating from «Позже»."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        user_id: UUID,
        *,
        card_id: str | None = None,
        film_id: int | None = None,
        catalog_item_id: int | None = None,
    ) -> PlannedUserCardDTO | None:
        entity: UserCard | None = None
        if film_id is not None:
            entity = (
                await self._session.execute(
                    select(UserCard).where(
                        UserCard.user_id == user_id,
                        UserCard.is_planned.is_(True),
                        UserCard.film_id == film_id,
                    )
                )
            ).scalar_one_or_none()
        elif catalog_item_id is not None:
            entity = (
                await self._session.execute(
                    select(UserCard).where(
                        UserCard.user_id == user_id,
                        UserCard.is_planned.is_(True),
                        UserCard.catalog_item_id == catalog_item_id,
                    )
                )
            ).scalar_one_or_none()
        elif card_id is not None:
            entity = await self._find_by_card_id(user_id, card_id)
        if entity is None:
            return None
        return self._to_dto(entity)

    async def _find_by_card_id(self, user_id: UUID, card_id: str) -> UserCard | None:
        stmt = select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.is_planned.is_(True),
        )
        if card_id.startswith('kp:'):
            external_id = card_id.removeprefix('kp:')
            stmt = stmt.where(
                UserCard.provider == CatalogProvider.kinopoisk,
                UserCard.external_id == external_id,
            )
        elif card_id.startswith('rawg:'):
            external_id = card_id.removeprefix('rawg:')
            stmt = stmt.where(
                UserCard.provider == CatalogProvider.rawg,
                UserCard.external_id == external_id,
            )
        elif card_id.startswith('custom:'):
            stmt = stmt.where(UserCard.source_url == card_id)
        else:
            return None
        return (await self._session.execute(stmt)).scalar_one_or_none()

    def _to_dto(self, entity: UserCard) -> PlannedUserCardDTO:
        company_raw = entity.company or CardCompany.alone.value
        try:
            company = CardCompany(company_raw)
        except ValueError:
            company = CardCompany.alone
        return PlannedUserCardDTO(
            user_card_id=int(entity.id),
            company=company,
            category_id=int(entity.category_id),
            watch_note=str(entity.watch_note or ''),
        )
