from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_feed_post_deep_link_block

logger = logging.getLogger(__name__)


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


@dataclass
class SendCoViewNudgeNotificationService:
    """Notifies unrated co-view participants after a partial session finalize."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        watch_session_id: UUID,
        initiator_user_id: UUID,
        feed_post_id: int,
        unrated_user_ids: list[UUID],
    ) -> None:
        if not unrated_user_ids:
            return

        async with disposable_async_session() as session:
            initiator = await session.get(User, initiator_user_id)
            if initiator is None:
                return

            actor_safe = html.escape(_format_actor_display(initiator))
            deep = html_feed_post_deep_link_block(feed_post_id, link_text='Открыть пост')
            caption = (
                f'🎬 <b>{actor_safe}</b> и друзья уже оценили совместный просмотр.\n\n'
                f'Добавь свою оценку — она попадёт в общий пост.\n\n'
                f'{deep}'
            )

            for recipient_id in unrated_user_ids:
                recipient = await session.get(User, recipient_id)
                if recipient is None or recipient.telegram_user_id is None:
                    logger.info(
                        'co-view nudge skipped (no chat) session=%s recipient=%s',
                        watch_session_id,
                        recipient_id,
                    )
                    continue
                await deliver_engagement_html_message(int(recipient.telegram_user_id), caption)
