"""Celery tasks: Telegram engagement notifications (reply + reaction)."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from uuid import UUID

import orjson
from celery import Celery

from models.reaction_target_kind import ReactionTargetKind
from services.telegram.notify_comment_reply import run_notify_comment_reply_safe
from services.telegram.notify_feed_post_comment_mention import (
    run_notify_feed_post_comment_mention_safe,
)
from services.telegram.notify_feed_post_mention import run_notify_feed_post_mention_safe
from services.telegram.notify_movie_card_comment_mention import (
    run_notify_movie_card_comment_mention_safe,
)
from services.telegram.notify_movie_card_root_comment import run_notify_movie_card_root_comment_safe
from services.telegram.notify_reaction_added import run_notify_reaction_added_safe
from services.telegram.notify_shared_movie_card import run_deliver_shared_movie_card_safe

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    """Run async code without conflicting with a running asyncio loop (e.g. FastAPI + Celery eager)."""

    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=120)


async def _notify_feed_post_mentions_async(
    actor_user_id: UUID,
    feed_post_id: int,
    recipient_user_ids: list[UUID],
) -> None:
    for rid in recipient_user_ids:
        await run_notify_feed_post_mention_safe(
            actor_user_id=actor_user_id,
            feed_post_id=feed_post_id,
            recipient_user_id=rid,
        )


async def _notify_movie_card_comment_mentions_async(
    actor_user_id: UUID,
    card_id: int,
    comment_id: int,
    recipient_user_ids: list[UUID],
) -> None:
    for rid in recipient_user_ids:
        await run_notify_movie_card_comment_mention_safe(
            actor_user_id=actor_user_id,
            card_id=card_id,
            comment_id=comment_id,
            recipient_user_id=rid,
        )


async def _notify_feed_post_comment_mentions_async(
    actor_user_id: UUID,
    feed_post_id: int,
    comment_id: int,
    recipient_user_ids: list[UUID],
) -> None:
    for rid in recipient_user_ids:
        await run_notify_feed_post_comment_mention_safe(
            actor_user_id=actor_user_id,
            feed_post_id=feed_post_id,
            comment_id=comment_id,
            recipient_user_id=rid,
        )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.telegram_engagement.notify_comment_reply')
    def notify_comment_reply_task(
        actor_user_id: str,
        card_id: int,
        parent_comment_id: int,
        reply_text: str,
    ) -> None:
        try:
            _run_async_isolated(
                run_notify_comment_reply_safe(
                    actor_user_id=UUID(actor_user_id),
                    card_id=card_id,
                    parent_comment_id=parent_comment_id,
                    reply_text=reply_text,
                )
            )
        except Exception:
            logger.exception('celery task notify_comment_reply_task failed')

    @app.task(name='tasks.telegram_engagement.notify_movie_card_root_comment')
    def notify_movie_card_root_comment_task(
        actor_user_id: str,
        card_id: int,
        comment_text: str,
    ) -> None:
        try:
            _run_async_isolated(
                run_notify_movie_card_root_comment_safe(
                    actor_user_id=UUID(actor_user_id),
                    card_id=card_id,
                    comment_text=comment_text,
                )
            )
        except Exception:
            logger.exception('celery task notify_movie_card_root_comment_task failed')

    @app.task(name='tasks.telegram_engagement.notify_reaction_added')
    def notify_reaction_added_task(
        actor_user_id: str,
        target_kind: str,
        target_id: int,
        reaction_type_id: int,
    ) -> None:
        try:
            kind = ReactionTargetKind(target_kind)
            _run_async_isolated(
                run_notify_reaction_added_safe(
                    actor_user_id=UUID(actor_user_id),
                    target_kind=kind,
                    target_id=target_id,
                    reaction_type_id=reaction_type_id,
                )
            )
        except Exception:
            logger.exception('celery task notify_reaction_added_task failed')

    @app.task(name='tasks.telegram_engagement.deliver_shared_movie_card')
    def deliver_shared_movie_card_task(
        actor_user_id: str,
        card_id: int,
        recipient_user_id: str,
        share_comment: str = '',
    ) -> None:
        try:
            _run_async_isolated(
                run_deliver_shared_movie_card_safe(
                    actor_user_id=UUID(actor_user_id),
                    card_id=card_id,
                    recipient_user_id=UUID(recipient_user_id),
                    share_comment=share_comment or '',
                )
            )
        except Exception:
            logger.exception('celery task deliver_shared_movie_card_task failed')

    @app.task(name='tasks.telegram_engagement.notify_feed_post_mentions')
    def notify_feed_post_mentions_task(
        actor_user_id: str,
        feed_post_id: int,
        recipient_user_ids_json: str,
    ) -> None:
        try:
            raw_ids = orjson.loads(recipient_user_ids_json)
            ids = [UUID(x) for x in raw_ids]
            if not ids:
                return
            _run_async_isolated(
                _notify_feed_post_mentions_async(
                    actor_user_id=UUID(actor_user_id),
                    feed_post_id=feed_post_id,
                    recipient_user_ids=ids,
                )
            )
        except Exception:
            logger.exception('celery task notify_feed_post_mentions_task failed')

    @app.task(name='tasks.telegram_engagement.notify_movie_card_comment_mentions')
    def notify_movie_card_comment_mentions_task(
        actor_user_id: str,
        card_id: int,
        comment_id: int,
        recipient_user_ids_json: str,
    ) -> None:
        try:
            raw_ids = orjson.loads(recipient_user_ids_json)
            ids = [UUID(x) for x in raw_ids]
            if not ids:
                return
            _run_async_isolated(
                _notify_movie_card_comment_mentions_async(
                    actor_user_id=UUID(actor_user_id),
                    card_id=card_id,
                    comment_id=comment_id,
                    recipient_user_ids=ids,
                )
            )
        except Exception:
            logger.exception('celery task notify_movie_card_comment_mentions_task failed')

    @app.task(name='tasks.telegram_engagement.notify_feed_post_comment_mentions')
    def notify_feed_post_comment_mentions_task(
        actor_user_id: str,
        feed_post_id: int,
        comment_id: int,
        recipient_user_ids_json: str,
    ) -> None:
        try:
            raw_ids = orjson.loads(recipient_user_ids_json)
            ids = [UUID(x) for x in raw_ids]
            if not ids:
                return
            _run_async_isolated(
                _notify_feed_post_comment_mentions_async(
                    actor_user_id=UUID(actor_user_id),
                    feed_post_id=feed_post_id,
                    comment_id=comment_id,
                    recipient_user_ids=ids,
                )
            )
        except Exception:
            logger.exception('celery task notify_feed_post_comment_mentions_task failed')
