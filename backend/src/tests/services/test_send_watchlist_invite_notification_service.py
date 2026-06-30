from __future__ import annotations

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from services.telegram.send_watchlist_invite_notification import (
    SendWatchlistInviteNotificationService,
)


async def _create_user(*, telegram_user_id: int, slug_suffix: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'wlinvite-{slug_suffix}',
            username=None,
            first_name='Test',
            last_name='User',
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_invite_notification_payload(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor = await _create_user(telegram_user_id=930001, slug_suffix='actor')
    invited = await _create_user(telegram_user_id=930002, slug_suffix='invited')
    sent: dict[str, object] = {}

    async def _fake_deliver(chat_id: int, html_text: str) -> None:
        sent['chat_id'] = chat_id
        sent['body'] = html_text

    monkeypatch.setattr(
        'services.telegram.send_watchlist_invite_notification.deliver_engagement_html_message',
        _fake_deliver,
    )

    service = SendWatchlistInviteNotificationService.build()
    payload = await service.execute(
        actor_user_id=actor.id,
        invited_user_id=invited.id,
        card_id='kp:123',
        provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 123}},
    )

    assert payload['user_id'] == invited.id
    assert payload['title'] == 'Invite to watch together'
    assert 'kp:123' in payload['deeplink']
    assert sent['chat_id'] == invited.telegram_user_id
