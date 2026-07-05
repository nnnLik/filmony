from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from const.text_limits import WATCH_NOTE_MAX_LEN
from models.card_enums import CardCompany
from models.watchlist_entry import WatchlistEntry
from services.cards.create_planned_user_card import CreatePlannedUserCardService
from services.telegram.send_watchlist_invite_notification import (
    SendWatchlistInviteNotificationService,
)
from services.text.spoiler_tokens import (
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)
from services.watchlist.assert_mutual_watch_partner import AssertMutualWatchPartnerService
from services.watchlist.normalize_watch_with_partners import (
    normalize_watch_with_user_ids,
    primary_watch_with_user_id,
    watch_with_user_ids_as_json,
)


def _normalize_watch_note(raw: str) -> str:
    s = (raw or '').strip()
    if len(s) > WATCH_NOTE_MAX_LEN:
        raise ValueError(f'watch note max length is {WATCH_NOTE_MAX_LEN}')
    try:
        return validate_spoiler_tokens(s)
    except SpoilerTokenValidationError as e:
        raise ValueError(str(e)) from e


@dataclass(frozen=True, slots=True)
class CreateWatchlistEntryResult:
    actor_entry: WatchlistEntry
    invited_entries: list[WatchlistEntry]

    @property
    def invited_entry(self) -> WatchlistEntry | None:
        return self.invited_entries[0] if self.invited_entries else None


@dataclass
class CreateWatchlistEntryService:
    """Creates a watchlist entry, planned card snippet, and optional friend invites."""

    _session: AsyncSession
    _planned_card_service: CreatePlannedUserCardService
    _invite_notification_service: SendWatchlistInviteNotificationService
    _assert_mutual_watch_partner_service: AssertMutualWatchPartnerService

    class WatchlistEntryAlreadyExistsError(Exception):
        pass

    WatchWithUserNotFoundError = AssertMutualWatchPartnerService.WatchWithUserNotFoundError
    NotMutualWatchPartnerError = AssertMutualWatchPartnerService.NotMutualWatchPartnerError

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _planned_card_service=CreatePlannedUserCardService.build(session),
            _invite_notification_service=SendWatchlistInviteNotificationService.build(),
            _assert_mutual_watch_partner_service=AssertMutualWatchPartnerService.build(session),
        )

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        card_id: str,
        provider_meta: dict,
        watch_tag: str,
        created_at: dt.datetime,
        company: CardCompany = CardCompany.alone,
        category_id: int | None = None,
        watch_note: str = '',
        watch_with_user_id: UUID | None = None,
        watch_with_user_ids: list[UUID] | None = None,
    ) -> CreateWatchlistEntryResult:
        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(dt.UTC).replace(tzinfo=None)

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

        for invitee_id in partner_ids:
            await self._assert_mutual_watch_partner_service.execute(
                actor_user_id=actor_user_id,
                watch_with_user_id=invitee_id,
            )

        actor_entry = WatchlistEntry(
            user_id=actor_user_id,
            card_id=card_id,
            provider_meta=provider_meta,
            watch_tag=watch_tag,
            watch_with_user_id=primary_partner_id,
            watch_with_user_ids=stored_ids_json,
            created_at=created_at,
        )
        self._session.add(actor_entry)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise self.WatchlistEntryAlreadyExistsError from exc

        await self._planned_card_service.execute(
            actor_user_id,
            card_id,
            provider_meta,
            company=effective_company,
            category_id=category_id,
            watch_note=normalized_note,
        )

        invited_entries: list[WatchlistEntry] = []
        invitee_planned_card_ids: dict[UUID, int] = {}
        for invitee_id in partner_ids:
            existing_invited = (
                await self._session.execute(
                    select(WatchlistEntry.id).where(
                        WatchlistEntry.user_id == invitee_id,
                        WatchlistEntry.card_id == card_id,
                    )
                )
            ).scalar_one_or_none()
            if existing_invited is not None:
                continue

            invited_entry = WatchlistEntry(
                user_id=invitee_id,
                card_id=card_id,
                provider_meta=provider_meta,
                watch_tag=watch_tag,
                watch_with_user_id=actor_user_id,
                watch_with_user_ids=[str(actor_user_id)],
                created_at=created_at,
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
                card_id,
                provider_meta,
                company=effective_company,
                category_id=None,
                watch_note=normalized_note,
            )
            invited_entries.append(invited_entry)
            invitee_planned_card_ids[invited_entry.user_id] = int(invited_planned_card.id)

        await self._session.commit()
        await self._session.refresh(actor_entry)
        for invited_entry in invited_entries:
            await self._session.refresh(invited_entry)
            await self._invite_notification_service.execute(
                actor_user_id=actor_user_id,
                invited_user_id=invited_entry.user_id,
                planned_user_card_id=invitee_planned_card_ids[invited_entry.user_id],
                card_id=card_id,
            )

        return CreateWatchlistEntryResult(
            actor_entry=actor_entry,
            invited_entries=invited_entries,
        )
