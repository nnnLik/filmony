"""Build and deliver subscribed-activity Telegram digest for one recipient."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscribed_activity_digest_state import SubscribedActivityDigestState
from models.user import User
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)
from services.telegram.build_subscribed_activity_digest_message import (
    BuildSubscribedActivityDigestMessageService,
)
from services.telegram.send_bot_message import SendTelegramBotMessageService
from services.telegram.subscribed_activity_digest_candidates import (
    DIGEST_INTERVAL,
    CollectSubscribedActivityDigestCandidatesService,
    DigestCandidate,
    SelectSubscribedActivityDigestItemsService,
    _ensure_naive_utc,
    digest_payload_hash,
)

logger = logging.getLogger(__name__)

_EMPTY_WINDOW_HASH = digest_payload_hash([])


class DigestDeliveryOutcome(StrEnum):
    sent = 'sent'
    skipped_no_telegram = 'skipped_no_telegram'
    skipped_no_subscriptions = 'skipped_no_subscriptions'
    skipped_no_candidates = 'skipped_no_candidates'
    skipped_chat_unavailable = 'skipped_chat_unavailable'
    delivery_failed = 'delivery_failed'


@dataclass(frozen=True, slots=True)
class DigestDeliveryResult:
    outcome: DigestDeliveryOutcome
    recipient_user_id: UUID
    payload_hash: str | None = None


def _compute_window(
    *,
    now: dt.datetime,
    state: SubscribedActivityDigestState | None,
) -> tuple[dt.datetime, dt.datetime]:
    now = _ensure_naive_utc(now)
    if state is not None and state.last_digest_sent_at is not None:
        window_start = _ensure_naive_utc(state.last_digest_sent_at)
    elif state is not None and state.last_processed_at is not None:
        window_start = _ensure_naive_utc(state.last_processed_at)
    else:
        window_start = now - DIGEST_INTERVAL
    return window_start, now


def _render_digest_html(
    *,
    items: list[DigestCandidate],
    pool: list[DigestCandidate],
    recipient_user_id: UUID,
    window_start: dt.datetime,
) -> str:
    return BuildSubscribedActivityDigestMessageService.build().execute(
        items=items,
        pool=pool,
        recipient_user_id=recipient_user_id,
        window_start=window_start,
    )


@dataclass
class SendSubscribedActivityTelegramDigestService:
    """Builds, sends, and persists subscribed-activity digest state for one recipient."""

    _session: AsyncSession
    _send_svc: SendTelegramBotMessageService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session, _send_svc=SendTelegramBotMessageService.build())

    async def execute(
        self,
        *,
        recipient_user_id: UUID,
        now: dt.datetime | None = None,
    ) -> DigestDeliveryResult:
        if now is None:
            now = _ensure_naive_utc(dt.datetime.now(tz=dt.UTC))
        else:
            now = _ensure_naive_utc(now)

        recipient = await self._session.get(User, recipient_user_id)
        if recipient is None or recipient.telegram_user_id is None:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_telegram,
                recipient_user_id=recipient_user_id,
            )

        following_ids = await ListFollowingUserIdsForFollowerUserService.build(
            self._session
        ).execute(recipient_user_id)
        if not following_ids:
            await self._mark_processed_empty(
                recipient_user_id=recipient_user_id,
                now=now,
                window_start=now - DIGEST_INTERVAL,
                window_end=now,
            )
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_subscriptions,
                recipient_user_id=recipient_user_id,
                payload_hash=_EMPTY_WINDOW_HASH,
            )

        state = await self._load_or_create_state(recipient_user_id)
        window_start, window_end = _compute_window(now=now, state=state)

        pool = await CollectSubscribedActivityDigestCandidatesService.build(self._session).execute(
            following_user_ids=following_ids,
            window_start=window_start,
            window_end=window_end,
        )
        selected = SelectSubscribedActivityDigestItemsService.build().execute(
            pool=pool,
            recipient_user_id=recipient_user_id,
            window_start=window_start,
        )

        if not selected:
            await self._mark_processed_empty(
                recipient_user_id=recipient_user_id,
                now=now,
                window_start=window_start,
                window_end=window_end,
            )
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_candidates,
                recipient_user_id=recipient_user_id,
                payload_hash=_EMPTY_WINDOW_HASH,
            )

        payload_hash = digest_payload_hash(selected)
        body = _render_digest_html(
            items=selected,
            pool=pool,
            recipient_user_id=recipient_user_id,
            window_start=window_start,
        )

        try:
            await self._send_svc.execute(
                int(recipient.telegram_user_id),
                body,
                parse_mode='HTML',
            )
        except SendTelegramBotMessageService.TelegramChatUnavailable:
            await self._mark_processed_empty(
                recipient_user_id=recipient_user_id,
                now=now,
                window_start=window_start,
                window_end=window_end,
            )
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_chat_unavailable,
                recipient_user_id=recipient_user_id,
                payload_hash=payload_hash,
            )
        except SendTelegramBotMessageService.TelegramDeliveryFailed:
            logger.warning(
                'subscribed activity digest delivery failed recipient=%s',
                recipient_user_id,
            )
            state.failed_attempts = int(state.failed_attempts) + 1
            state.last_error_at = now
            await self._session.commit()
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.delivery_failed,
                recipient_user_id=recipient_user_id,
                payload_hash=payload_hash,
            )

        state.last_digest_sent_at = now
        state.last_successful_delivery_at = now
        state.last_processed_at = now
        state.last_digest_window_start = window_start
        state.last_digest_window_end = window_end
        state.last_digest_payload_hash = payload_hash
        state.failed_attempts = 0
        state.last_error_at = None
        await self._session.commit()

        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.sent,
            recipient_user_id=recipient_user_id,
            payload_hash=payload_hash,
        )

    async def _load_or_create_state(
        self,
        recipient_user_id: UUID,
    ) -> SubscribedActivityDigestState:
        row = (
            await self._session.execute(
                select(SubscribedActivityDigestState).where(
                    SubscribedActivityDigestState.recipient_user_id == recipient_user_id
                )
            )
        ).scalar_one_or_none()
        if row is not None:
            return row
        state = SubscribedActivityDigestState(recipient_user_id=recipient_user_id)
        self._session.add(state)
        await self._session.flush()
        return state

    async def _mark_processed_empty(
        self,
        *,
        recipient_user_id: UUID,
        now: dt.datetime,
        window_start: dt.datetime,
        window_end: dt.datetime,
    ) -> None:
        state = await self._load_or_create_state(recipient_user_id)
        state.last_processed_at = now
        state.last_digest_window_start = window_start
        state.last_digest_window_end = window_end
        state.last_digest_payload_hash = _EMPTY_WINDOW_HASH
        await self._session.commit()


async def run_subscribed_activity_digest_for_recipient_safe(
    *,
    recipient_user_id: UUID,
) -> DigestDeliveryResult:
    from core.database import disposable_async_session

    try:
        async with disposable_async_session() as session:
            return await SendSubscribedActivityTelegramDigestService.build(session).execute(
                recipient_user_id=recipient_user_id,
            )
    except Exception:
        logger.exception(
            'subscribed activity digest failed recipient=%s',
            recipient_user_id,
        )
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.delivery_failed,
            recipient_user_id=recipient_user_id,
        )
