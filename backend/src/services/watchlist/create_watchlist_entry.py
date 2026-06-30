from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.watchlist_entry import WatchlistEntry
from services.feed_posts.create_watchlist_feed_post import CreateWatchlistFeedPostService
from services.telegram.send_watchlist_invite_notification import (
    SendWatchlistInviteNotificationService,
)
from services.watchlist.assert_mutual_watch_partner import AssertMutualWatchPartnerService


@dataclass(frozen=True, slots=True)
class CreateWatchlistEntryResult:
    actor_entry: WatchlistEntry
    invited_entry: WatchlistEntry | None


@dataclass
class CreateWatchlistEntryService:
    """Creates a watchlist entry and optional friend invite entry."""

    _session: AsyncSession
    _feed_post_service: CreateWatchlistFeedPostService
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
            _feed_post_service=CreateWatchlistFeedPostService.build(session),
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
        watch_with_user_id: UUID | None,
        created_at: dt.datetime,
    ) -> CreateWatchlistEntryResult:
        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(dt.UTC).replace(tzinfo=None)
        if watch_with_user_id is not None and watch_with_user_id != actor_user_id:
            await self._assert_mutual_watch_partner_service.execute(
                actor_user_id=actor_user_id,
                watch_with_user_id=watch_with_user_id,
            )
        actor_entry = WatchlistEntry(
            user_id=actor_user_id,
            card_id=card_id,
            provider_meta=provider_meta,
            watch_tag=watch_tag,
            watch_with_user_id=watch_with_user_id,
            created_at=created_at,
        )
        self._session.add(actor_entry)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise self.WatchlistEntryAlreadyExistsError from exc

        await self._feed_post_service.execute(
            user_id=actor_user_id,
            card_id=card_id,
            provider_meta=provider_meta,
        )

        invited_entry = None
        if watch_with_user_id is not None and watch_with_user_id != actor_user_id:
            existing_invited = (
                await self._session.execute(
                    select(WatchlistEntry.id).where(
                        WatchlistEntry.user_id == watch_with_user_id,
                        WatchlistEntry.card_id == card_id,
                    )
                )
            ).scalar_one_or_none()
            if existing_invited is None:
                invited_entry = WatchlistEntry(
                    user_id=watch_with_user_id,
                    card_id=card_id,
                    provider_meta=provider_meta,
                    watch_tag=watch_tag,
                    watch_with_user_id=actor_user_id,
                    created_at=created_at,
                )
                try:
                    async with self._session.begin_nested():
                        self._session.add(invited_entry)
                        await self._session.flush()
                except IntegrityError:
                    self._session.expunge(invited_entry)
                    invited_entry = None

        await self._session.commit()
        await self._session.refresh(actor_entry)
        if invited_entry is not None:
            await self._session.refresh(invited_entry)
            await self._invite_notification_service.execute(
                actor_user_id=actor_user_id,
                invited_user_id=watch_with_user_id,
                card_id=card_id,
                provider_meta=provider_meta,
            )

        return CreateWatchlistEntryResult(
            actor_entry=actor_entry,
            invited_entry=invited_entry,
        )
