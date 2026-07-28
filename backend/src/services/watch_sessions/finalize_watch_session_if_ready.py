from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from models.watch_session import WatchSession
from models.watch_session_enums import WatchSessionStatus
from services.telegram.send_coview_nudge_notification import SendCoViewNudgeNotificationService
from services.watch_sessions.create_coview_feed_post import CreateCoViewFeedPostService
from services.watch_sessions.list_co_view_splits import _parse_participant_ids

FINALIZE_TIMEOUT = dt.timedelta(hours=48)


@dataclass
class FinalizeWatchSessionIfReadyService:
    """Finalizes a co-view session when everyone rated or after a 48h partial timeout."""

    _session: AsyncSession
    _create_post_service: CreateCoViewFeedPostService
    _nudge_service: SendCoViewNudgeNotificationService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _create_post_service=CreateCoViewFeedPostService.build(session),
            _nudge_service=SendCoViewNudgeNotificationService.build(),
        )

    async def execute(
        self,
        *,
        watch_session_id: UUID,
        now: dt.datetime | None = None,
    ) -> bool:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=dt.UTC)
        else:
            now = now.astimezone(dt.UTC)

        session = await self._session.get(WatchSession, watch_session_id)
        if session is None:
            return False
        if session.status == WatchSessionStatus.done or session.feed_post_id is not None:
            return False

        participant_ids = _parse_participant_ids(session.participant_user_ids)
        if not participant_ids:
            return False

        rated_by_user = await self._load_rated_cards(
            participant_ids,
            anchor_film_id=session.anchor_film_id,
            anchor_catalog_item_id=session.anchor_catalog_item_id,
        )
        rated_count = len(rated_by_user)
        all_rated = rated_count == len(participant_ids)
        timeout_ready = False
        if session.first_rated_at is not None:
            first_at = session.first_rated_at
            if first_at.tzinfo is None:
                first_at = first_at.replace(tzinfo=dt.UTC)
            else:
                first_at = first_at.astimezone(dt.UTC)
            timeout_ready = now - first_at >= FINALIZE_TIMEOUT and rated_count >= 2

        if not all_rated and not timeout_ready:
            return False

        initiator_id = session.initiator_user_id
        initiator_card = rated_by_user.get(initiator_id)
        if initiator_card is None:
            return False

        unrated_ids = [uid for uid in participant_ids if uid not in rated_by_user]
        should_nudge = not all_rated and session.nudge_sent_at is None and bool(unrated_ids)
        if should_nudge:
            session.nudge_sent_at = now

        post = await self._create_post_service.execute(
            initiator_user_id=initiator_id,
            initiator_rated_card_id=int(initiator_card.id),
            watch_session_id=session.id,
        )
        session.feed_post_id = int(post.id)
        session.status = WatchSessionStatus.done
        await self._session.commit()

        if should_nudge:
            await self._nudge_service.execute(
                watch_session_id=session.id,
                initiator_user_id=initiator_id,
                feed_post_id=int(post.id),
                unrated_user_ids=unrated_ids,
            )

        return True

    async def _load_rated_cards(
        self,
        participant_ids: list[UUID],
        *,
        anchor_film_id: int | None,
        anchor_catalog_item_id: int | None,
    ) -> dict[UUID, UserCard]:
        out: dict[UUID, UserCard] = {}
        for participant_id in participant_ids:
            stmt = select(UserCard).where(
                UserCard.user_id == participant_id,
                UserCard.is_planned.is_(False),
            )
            if anchor_film_id is not None:
                stmt = stmt.where(UserCard.film_id == anchor_film_id)
            elif anchor_catalog_item_id is not None:
                stmt = stmt.where(UserCard.catalog_item_id == anchor_catalog_item_id)
            else:
                continue
            stmt = stmt.order_by(UserCard.completed_at.desc(), UserCard.id.desc()).limit(1)
            card = (await self._session.execute(stmt)).scalar_one_or_none()
            if card is not None:
                out[participant_id] = card
        return out
