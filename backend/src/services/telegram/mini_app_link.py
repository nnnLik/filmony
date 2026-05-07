"""Build deep links into the Mini App from the bot username."""

from __future__ import annotations

import html

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


def html_card_deep_link_block(card_id: int) -> str:
    """Single prominent block: emoji + link to the card (Mini App start_param c<id>)."""
    url = telegram_mini_app_card_url(card_id)
    if url is None:
        return '📱 Откройте Mini App из Telegram'
    esc_url = html.escape(url, quote=True)
    return f'🎬 <a href="{esc_url}">Карточка №{card_id}</a>'
