from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.film import Film
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_watch_party_deep_link_block
from services.telegram.send_bot_message import SendTelegramBotMessageService
from utils.http_url import normalize_absolute_http_url

logger = logging.getLogger(__name__)


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _payload_stub(
    *,
    invited_user_id: UUID,
    actor_user_id: UUID,
    party_id: UUID,
    invite_slug: str,
    body: str | None = None,
) -> dict:
    out: dict = {
        'user_id': invited_user_id,
        'title': 'Приглашение в watch party',
        'deeplink': f'filmony://watch-party/{invite_slug}',
        'metadata': {
            'actor_user_id': actor_user_id,
            'party_id': str(party_id),
            'invite_slug': invite_slug,
        },
    }
    if body is not None:
        out['body'] = body
    return out


@dataclass
class SendWatchPartyInviteNotificationService:
    """Send a Telegram notification inviting a mutual follow to a watch party."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        invited_user_id: UUID,
        party_id: UUID,
        invite_slug: str,
        film_id: int,
    ) -> dict:
        async with disposable_async_session() as session:
            actor = await session.get(User, actor_user_id)
            invited = await session.get(User, invited_user_id)
            film = await session.get(Film, film_id)
            if actor is None or invited is None or invited.telegram_user_id is None:
                return _payload_stub(
                    invited_user_id=invited_user_id,
                    actor_user_id=actor_user_id,
                    party_id=party_id,
                    invite_slug=invite_slug,
                )

            title = (film.title if film is not None else '').strip() or 'Фильм'
            actor_safe = html.escape(_format_actor_display(actor))
            title_safe = html.escape(title)
            deep = html_watch_party_deep_link_block(
                invite_slug, link_text='Присоединиться к просмотру'
            )
            caption = (
                f'🎬 <b>{actor_safe}</b> приглашает смотреть вместе\n\n'
                f'<b>{title_safe}</b>\n\n'
                f'{deep}'
            )
            poster_url = film.poster_url if film is not None else None
            poster = normalize_absolute_http_url(poster_url)
            send_svc = SendTelegramBotMessageService.build()
            chat_id = int(invited.telegram_user_id)
            if poster is not None:
                try:
                    await send_svc.send_photo(chat_id, poster, caption, parse_mode='HTML')
                except SendTelegramBotMessageService.TelegramChatUnavailable:
                    logger.info(
                        'watch party invite skipped (no chat) recipient=%s party=%s',
                        invited_user_id,
                        party_id,
                    )
                    return _payload_stub(
                        invited_user_id=invited_user_id,
                        actor_user_id=actor_user_id,
                        party_id=party_id,
                        invite_slug=invite_slug,
                    )
                except SendTelegramBotMessageService.TelegramDeliveryFailed:
                    logger.warning(
                        'watch party invite sendPhoto failed party=%s',
                        party_id,
                    )
                else:
                    return _payload_stub(
                        invited_user_id=invited_user_id,
                        actor_user_id=actor_user_id,
                        party_id=party_id,
                        invite_slug=invite_slug,
                        body=caption,
                    )

            await deliver_engagement_html_message(chat_id, caption)
            return _payload_stub(
                invited_user_id=invited_user_id,
                actor_user_id=actor_user_id,
                party_id=party_id,
                invite_slug=invite_slug,
                body=caption,
            )
