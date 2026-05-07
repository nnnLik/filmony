"""Build deep links into the Mini App from the bot username."""

from __future__ import annotations

from conf import settings


def telegram_mini_app_card_url(card_id: int) -> str | None:
    """Returns https://t.me/<bot>?startapp=c<card_id> when bot username is configured."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    return f'https://t.me/{name}?startapp=c{card_id}'
