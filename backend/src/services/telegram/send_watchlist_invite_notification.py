from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


@dataclass
class SendWatchlistInviteNotificationService:
    """Send a Telegram notification for watchlist invites."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        invited_user_id: UUID,
        card_id: str,
        provider_meta: dict,
    ) -> dict:
        async with disposable_async_session() as session:
            actor = await session.get(User, actor_user_id)
            invited = await session.get(User, invited_user_id)
            if actor is None or invited is None or invited.telegram_user_id is None:
                return {
                    'user_id': invited_user_id,
                    'title': 'Invite to watch together',
                    'deeplink': f'filmony://watchlist/{card_id}',
                    'metadata': {
                        'actor_user_id': actor_user_id,
                        'provider_meta': provider_meta,
                    },
                }

            actor_name = html.escape(_format_actor_display(actor))
            title = 'Invite to watch together'
            body = f'🎬 <b>{actor_name}</b> invited you to watch together.'
            deeplink = f'filmony://watchlist/{card_id}'
            await deliver_engagement_html_message(int(invited.telegram_user_id), body)
            return {
                'user_id': invited_user_id,
                'title': title,
                'body': body,
                'deeplink': deeplink,
                'metadata': {
                    'actor_user_id': actor_user_id,
                    'provider_meta': provider_meta,
                },
            }
