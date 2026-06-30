from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_enums import CardCompany
from models.user_card import UserCard
from models.watchlist_entry import WatchlistEntry
from services.cards.create_planned_user_card import CreatePlannedUserCardService
from services.cards.get_planned_user_card import GetPlannedUserCardService
from services.telegram.send_watchlist_invite_notification import (
    SendWatchlistInviteNotificationService,
)
from services.watchlist.assert_mutual_watch_partner import AssertMutualWatchPartnerService
from services.watchlist.normalize_watch_with_partners import (
    normalize_watch_with_user_ids,
    primary_watch_with_user_id,
    watch_with_user_ids_as_json,
)


def _normalize_watch_note(raw: str) -> str:
    return (raw or '').strip()[:500]


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


@dataclass(frozen=True, slots=True)
class UpdateWatchlistEntryResult:
    actor_entry: WatchlistEntry
    invited_entries: list[WatchlistEntry]


@dataclass
class UpdateWatchlistEntryService:
    """Updates watchlist metadata, planned card fields, and partner invites/removals."""

    _session: AsyncSession
    _planned_card_service: CreatePlannedUserCardService
    _get_planned_card_service: GetPlannedUserCardService
    _invite_notification_service: SendWatchlistInviteNotificationService
    _assert_mutual_watch_partner_service: AssertMutualWatchPartnerService

    class WatchlistEntryNotFoundError(Exception):
        pass

    WatchWithUserNotFoundError = AssertMutualWatchPartnerService.WatchWithUserNotFoundError
    NotMutualWatchPartnerError = AssertMutualWatchPartnerService.NotMutualWatchPartnerError

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _planned_card_service=CreatePlannedUserCardService.build(session),
            _get_planned_card_service=GetPlannedUserCardService.build(session),
            _invite_notification_service=SendWatchlistInviteNotificationService.build(),
            _assert_mutual_watch_partner_service=AssertMutualWatchPartnerService.build(session),
        )

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        entry_id: int,
        company: CardCompany = CardCompany.alone,
        category_id: int | None = None,
        watch_note: str = '',
        watch_with_user_id: UUID | None = None,
        watch_with_user_ids: list[UUID] | None = None,
    ) -> UpdateWatchlistEntryResult:
        entry = await self._session.get(WatchlistEntry, entry_id)
        if entry is None or entry.user_id != actor_user_id:
            raise self.WatchlistEntryNotFoundError

        old_partner_ids = set(_partner_ids_from_entry(entry, actor_user_id))
        partner_ids = normalize_watch_with_user_ids(
            actor_user_id=actor_user_id,
            company=company,
            watch_with_user_ids=watch_with_user_ids,
            watch_with_user_id=watch_with_user_id,
        )
        effective_company = company
        if effective_company == CardCompany.alone and partner_ids:
            effective_company = CardCompany.friends
        primary_partner_id = primary_watch_with_user_id(partner_ids)
        stored_ids_json = watch_with_user_ids_as_json(partner_ids)
        normalized_note = _normalize_watch_note(watch_note)
        new_partner_ids = set(partner_ids)

        for invitee_id in partner_ids:
            await self._assert_mutual_watch_partner_service.execute(
                actor_user_id=actor_user_id,
                watch_with_user_id=invitee_id,
            )

        entry.watch_with_user_id = primary_partner_id
        entry.watch_with_user_ids = stored_ids_json

        await self._planned_card_service.execute(
            actor_user_id,
            entry.card_id,
            entry.provider_meta,
            company=effective_company,
            category_id=category_id,
            watch_note=normalized_note,
        )

        removed_partner_ids = old_partner_ids - new_partner_ids
        for removed_id in removed_partner_ids:
            await self._remove_invited_partner(
                actor_user_id=actor_user_id,
                partner_user_id=removed_id,
                card_id=entry.card_id,
            )

        invited_entries: list[WatchlistEntry] = []
        invitee_planned_card_ids: dict[UUID, int] = {}
        added_partner_ids = new_partner_ids - old_partner_ids
        for invitee_id in partner_ids:
            if invitee_id not in added_partner_ids:
                continue

            existing_invited = (
                await self._session.execute(
                    select(WatchlistEntry.id).where(
                        WatchlistEntry.user_id == invitee_id,
                        WatchlistEntry.card_id == entry.card_id,
                    )
                )
            ).scalar_one_or_none()
            if existing_invited is not None:
                continue

            invited_entry = WatchlistEntry(
                user_id=invitee_id,
                card_id=entry.card_id,
                provider_meta=entry.provider_meta,
                watch_tag=entry.watch_tag,
                watch_with_user_id=actor_user_id,
                watch_with_user_ids=[str(actor_user_id)],
                created_at=entry.created_at,
            )
            try:
                async with self._session.begin_nested():
                    self._session.add(invited_entry)
                    await self._session.flush()
            except IntegrityError:
                self._session.expunge(invited_entry)
                continue

            invited_planned_card = await self._planned_card_service.execute(
                invitee_id,
                entry.card_id,
                entry.provider_meta,
                company=effective_company,
                category_id=None,
                watch_note=normalized_note,
            )
            invited_entries.append(invited_entry)
            invitee_planned_card_ids[invited_entry.user_id] = int(invited_planned_card.id)

        await self._session.commit()
        await self._session.refresh(entry)
        for invited_entry in invited_entries:
            await self._session.refresh(invited_entry)
            await self._invite_notification_service.execute(
                actor_user_id=actor_user_id,
                invited_user_id=invited_entry.user_id,
                planned_user_card_id=invitee_planned_card_ids[invited_entry.user_id],
                card_id=entry.card_id,
            )

        return UpdateWatchlistEntryResult(
            actor_entry=entry,
            invited_entries=invited_entries,
        )

    async def _remove_invited_partner(
        self,
        *,
        actor_user_id: UUID,
        partner_user_id: UUID,
        card_id: str,
    ) -> None:
        invite_entry = (
            await self._session.execute(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == partner_user_id,
                    WatchlistEntry.card_id == card_id,
                    WatchlistEntry.watch_with_user_id == actor_user_id,
                )
            )
        ).scalar_one_or_none()
        if invite_entry is None:
            return

        planned_dto = await self._get_planned_card_service.execute(
            partner_user_id,
            card_id=card_id,
        )
        await self._session.delete(invite_entry)
        if planned_dto is not None:
            planned_card = await self._session.get(UserCard, planned_dto.user_card_id)
            if planned_card is not None and planned_card.is_planned:
                await self._session.delete(planned_card)
