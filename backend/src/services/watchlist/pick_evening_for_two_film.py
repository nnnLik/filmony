from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from models.user_subscription import UserSubscription
from services.watchlist.list_watchlist_overlaps import (
    ListWatchlistOverlapsService,
    WatchlistOverlapItem,
    WatchlistOverlapPartner,
)


@dataclass(frozen=True, slots=True)
class EveningForTwoPick:
    entry_id: int
    film_id: int
    title: str
    poster_url: str | None
    partner: WatchlistOverlapPartner


@dataclass
class PickEveningForTwoFilmService:
    """Picks a shared watchlist film for two mutual subscribers who have not rated it."""

    _session: AsyncSession

    class PickEveningForTwoFilmServiceError(Exception):
        pass

    class PartnerNotMutual(PickEveningForTwoFilmServiceError):
        pass

    class NoEveningPick(PickEveningForTwoFilmServiceError):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, actor_user_id: UUID, partner_user_id: UUID) -> EveningForTwoPick:
        mutual_ids = await self._load_mutual_partner_ids(actor_user_id)
        if partner_user_id not in mutual_ids:
            raise self.PartnerNotMutual

        overlap_page = await ListWatchlistOverlapsService.build(self._session).execute(
            actor_user_id,
            limit=50,
            mutual_partner_ids=mutual_ids,
        )
        candidates = [
            item
            for item in overlap_page.items
            if item.film_id is not None and _partner_in_item(item, partner_user_id)
        ]
        if not candidates:
            raise self.NoEveningPick

        film_ids = [int(item.film_id) for item in candidates if item.film_id is not None]
        rated_film_ids = await self._load_meaningful_rated_film_ids(
            [actor_user_id, partner_user_id],
            film_ids,
        )
        eligible = [item for item in candidates if int(item.film_id) not in rated_film_ids]
        if not eligible:
            raise self.NoEveningPick

        picked = _pick_item(eligible, actor_user_id, partner_user_id)
        partner = _find_partner(picked, partner_user_id)
        if partner is None or picked.film_id is None:
            raise self.NoEveningPick

        return EveningForTwoPick(
            entry_id=int(picked.entry_id),
            film_id=int(picked.film_id),
            title=picked.title,
            poster_url=picked.poster_url,
            partner=partner,
        )

    async def _load_mutual_partner_ids(self, actor_user_id: UUID) -> set[UUID]:
        followers_subq = select(UserSubscription.follower_user_id).where(
            UserSubscription.following_user_id == actor_user_id
        )
        rows = (
            (
                await self._session.execute(
                    select(UserSubscription.following_user_id).where(
                        UserSubscription.follower_user_id == actor_user_id,
                        UserSubscription.following_user_id.in_(followers_subq),
                    )
                )
            )
            .scalars()
            .all()
        )
        return set(rows)

    async def _load_meaningful_rated_film_ids(
        self,
        user_ids: list[UUID],
        film_ids: list[int],
    ) -> set[int]:
        if not user_ids or not film_ids:
            return set()
        rows = (
            (
                await self._session.execute(
                    select(UserCard.film_id)
                    .where(
                        UserCard.user_id.in_(user_ids),
                        UserCard.film_id.in_(film_ids),
                        UserCard.is_planned.is_(False),
                        UserCard.rating >= 1.0,
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        return {int(film_id) for film_id in rows if film_id is not None}


def _partner_in_item(item: WatchlistOverlapItem, partner_user_id: UUID) -> bool:
    return any(partner.user_id == partner_user_id for partner in item.partners)


def _find_partner(
    item: WatchlistOverlapItem,
    partner_user_id: UUID,
) -> WatchlistOverlapPartner | None:
    for partner in item.partners:
        if partner.user_id == partner_user_id:
            return partner
    return None


def _pick_item(
    items: list[WatchlistOverlapItem],
    actor_user_id: UUID,
    partner_user_id: UUID,
) -> WatchlistOverlapItem:
    if len(items) == 1:
        return items[0]
    seed_material = f'{actor_user_id}:{partner_user_id}'.encode()
    seed_int = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], 'big')
    rng = random.Random(seed_int)
    return rng.choice(items)
