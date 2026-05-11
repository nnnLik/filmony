from __future__ import annotations

import html

from conf import settings

_DEFAULT_LINK_LABEL = 'Открыть в Filmony'
_DIRECT_LINK_SEGMENT = 'app'


def telegram_mini_app_card_url(card_id: int) -> str | None:
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=c{card_id}'


def telegram_mini_app_feed_post_url(post_id: int) -> str | None:
    """Deep link into Mini App feed with highlight target (handled by start_param ``p<id>``)."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=p{post_id}'


def html_card_deep_link_block(card_id: int, *, link_text: str | None = None) -> str:
    url = telegram_mini_app_card_url(card_id)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or _DEFAULT_LINK_LABEL)
    return f'🔗 <a href="{esc_url}">{label}</a>'


def html_feed_post_deep_link_block(post_id: int, *, link_text: str | None = None) -> str:
    url = telegram_mini_app_feed_post_url(post_id)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or 'Открыть пост в ленте')
    return f'🔗 <a href="{esc_url}">{label}</a>'
