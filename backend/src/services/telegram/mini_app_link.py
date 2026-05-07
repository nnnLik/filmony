"""Build deep links into the Mini App from the bot username."""

from __future__ import annotations

import html

from conf import settings

# Текст ссылки без «карточка» и без внутреннего id — только призыв открыть приложение.
_DEFAULT_LINK_LABEL = 'Открыть в Filmony'


def telegram_mini_app_card_url(card_id: int) -> str | None:
    """Direct Link Mini App: ``https://t.me/<bot>[/<short>]?startapp=c<card_id>``."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    short = settings.telegram.mini_app_short_name
    if isinstance(short, str) and (sn := short.strip()):
        base = f'https://t.me/{name}/{sn.lstrip("/")}'
    else:
        base = f'https://t.me/{name}'
    return f'{base}?startapp=c{card_id}'


def html_card_deep_link_block(card_id: int, *, link_text: str | None = None) -> str:
    """Кликабельная ссылка в HTML для Telegram; подпись без id карточки."""
    url = telegram_mini_app_card_url(card_id)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or _DEFAULT_LINK_LABEL)
    return f'🔗 <a href="{esc_url}">{label}</a>'
