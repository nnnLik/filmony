from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from models.watchlist_entry import WatchlistEntry
from services.watchlist.list_user_watchlist_entries import (
    ListUserWatchlistEntriesService,
    _collect_hydration_keys,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class WatchlistOverlapPartner:
    user_id: UUID
    slug: str
    display_name: str | None
    avatar_url: str | None


@dataclass(frozen=True, slots=True)
class WatchlistOverlapItem:
    entry_id: int
    title: str
    poster_url: str | None
    card_id: str
    film_id: int | None
    catalog_item_id: int | None
    watch_with_user_ids: list[UUID]
    company: str
    watch_note: str
    partners: list[WatchlistOverlapPartner]


@dataclass(frozen=True, slots=True)
class WatchlistOverlapPage:
    items: list[WatchlistOverlapItem]


@dataclass
class ListWatchlistOverlapsService:
    """Lists watchlist titles the user shares with mutual subscription partners."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, actor_user_id: UUID, *, limit: int) -> WatchlistOverlapPage:
        cap = max(1, min(limit, 50))
        mutual_ids = await self._load_mutual_partner_ids(actor_user_id)
        if not mutual_ids:
            return WatchlistOverlapPage(items=[])

        actor_entries = await self._fetch_overlapping_actor_entries(
            actor_user_id,
            mutual_ids,
            cap,
        )
        if not actor_entries:
            return WatchlistOverlapPage(items=[])

        card_ids = [entry.card_id for entry in actor_entries]
        partners_by_card = await self._load_partners_by_card_id(mutual_ids, card_ids)

        list_svc = ListUserWatchlistEntriesService(self._session)
        maps = await list_svc._load_hydration_maps(_collect_hydration_keys(actor_entries))
        planned_by_key = await list_svc._load_planned_user_card_ids_by_key(actor_user_id)
        planned_meta = await self._load_planned_meta_by_card_id(actor_user_id, planned_by_key)

        items: list[WatchlistOverlapItem] = []
        for entry in actor_entries:
            partners = partners_by_card.get(entry.card_id, [])
            if not partners:
                continue
            hydrated = list_svc._hydrate_entry(entry, maps, planned_by_key)
            existing_partners = _partner_ids_from_entry(entry, actor_user_id)
            meta = planned_meta.get(entry.card_id, ('alone', ''))
            items.append(
                WatchlistOverlapItem(
                    entry_id=int(entry.id),
                    title=hydrated.title,
                    poster_url=hydrated.poster_url,
                    card_id=hydrated.card_id,
                    film_id=hydrated.film_id,
                    catalog_item_id=hydrated.catalog_item_id,
                    watch_with_user_ids=existing_partners,
                    company=str(meta[0]),
                    watch_note=str(meta[1]),
                    partners=partners,
                )
            )

        return WatchlistOverlapPage(items=items)

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

    async def _fetch_overlapping_actor_entries(
        self,
        actor_user_id: UUID,
        mutual_ids: set[UUID],
        cap: int,
    ) -> list[WatchlistEntry]:
        partner_card_ids = (
            select(WatchlistEntry.card_id).where(WatchlistEntry.user_id.in_(mutual_ids)).distinct()
        )
        stmt = (
            select(WatchlistEntry)
            .where(
                WatchlistEntry.user_id == actor_user_id,
                WatchlistEntry.card_id.in_(partner_card_ids),
            )
            .order_by(WatchlistEntry.created_at.desc(), WatchlistEntry.id.desc())
            .limit(cap)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _load_planned_meta_by_card_id(
        self,
        actor_user_id: UUID,
        planned_by_key: dict[str, int],
    ) -> dict[str, tuple[str, str]]:
        if not planned_by_key:
            return {}
        list(planned_by_key.keys())
        card_row_ids = list(planned_by_key.values())
        rows = (
            (
                await self._session.execute(
                    select(UserCard).where(
                        UserCard.user_id == actor_user_id,
                        UserCard.id.in_(card_row_ids),
                        UserCard.is_planned.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )
        by_id = {int(row.id): row for row in rows}
        out: dict[str, tuple[str, str]] = {}
        for card_key, user_card_id in planned_by_key.items():
            card = by_id.get(int(user_card_id))
            if card is None:
                continue
            company_raw = card.company
            company = company_raw.value if hasattr(company_raw, 'value') else str(company_raw)
            out[card_key] = (company, str(card.watch_note or ''))
        return out

    async def _load_partners_by_card_id(
        self,
        mutual_ids: set[UUID],
        card_ids: list[str],
    ) -> dict[str, list[WatchlistOverlapPartner]]:
        if not card_ids:
            return {}

        rows = (
            await self._session.execute(
                select(WatchlistEntry, User)
                .join(User, User.id == WatchlistEntry.user_id)
                .where(
                    WatchlistEntry.user_id.in_(mutual_ids),
                    WatchlistEntry.card_id.in_(card_ids),
                )
                .order_by(User.display_name.nulls_last(), User.profile_slug)
            )
        ).all()

        out: dict[str, list[WatchlistOverlapPartner]] = defaultdict(list)
        seen: dict[str, set[UUID]] = defaultdict(set)
        for entry, user in rows:
            if user.id in seen[entry.card_id]:
                continue
            seen[entry.card_id].add(user.id)
            out[entry.card_id].append(
                WatchlistOverlapPartner(
                    user_id=user.id,
                    slug=user.profile_slug,
                    display_name=user.display_name,
                    avatar_url=user.photo_url,
                )
            )
        return dict(out)


def _partner_ids_from_entry(entry: WatchlistEntry, actor_user_id: UUID) -> list[UUID]:
    partner_ids: list[UUID] = []
    seen: set[UUID] = {actor_user_id}
    for raw in entry.watch_with_user_ids or []:
        try:
            partner_id = UUID(str(raw))
        except (TypeError, ValueError):
            continue
        if partner_id in seen:
            continue
        seen.add(partner_id)
        partner_ids.append(partner_id)
    if entry.watch_with_user_id is not None and entry.watch_with_user_id not in seen:
        partner_ids.append(entry.watch_with_user_id)
    return partner_ids
