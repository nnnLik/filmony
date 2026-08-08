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


def telegram_mini_app_film_url(film_id: int) -> str | None:
    """Deep link into Mini App film community page (handled by start_param ``f<id>``)."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=f{film_id}'


def telegram_mini_app_taste_quiz_url(invite_token: str) -> str | None:
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=tq{invite_token}'


def telegram_mini_app_recap_url(*, year: int, month: int) -> str | None:
    """Deep link into monthly recap screen (handled by start_param ``mr{year}-{month}``)."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=mr{year}-{month}'


def telegram_mini_app_weekly_digest_url(*, period_key: str) -> str | None:
    """Deep link into weekly digest screen (handled by start_param ``wd{period_key}``)."""
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    base = f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'
    return f'{base}?startapp=wd{period_key}'


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


def telegram_mini_app_url() -> str | None:
    raw = settings.telegram.bot_username
    if raw is None:
        return None
    name = raw.strip().lstrip('@')
    if not name:
        return None
    return f'https://t.me/{name}/{_DIRECT_LINK_SEGMENT}'


def html_film_deep_link_block(film_id: int, *, link_text: str | None = None) -> str:
    url = telegram_mini_app_film_url(film_id)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or _DEFAULT_LINK_LABEL)
    return f'🔗 <a href="{esc_url}">{label}</a>'


def html_recap_deep_link_block(*, year: int, month: int, link_text: str | None = None) -> str:
    url = telegram_mini_app_recap_url(year=year, month=month)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or 'Посмотреть итоги месяца')
    return f'🔗 <a href="{esc_url}">{label}</a>'


def html_weekly_digest_deep_link_block(
    *,
    period_key: str,
    link_text: str | None = None,
) -> str:
    url = telegram_mini_app_weekly_digest_url(period_key=period_key)
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or 'Открыть сводку недели')
    return f'🔗 <a href="{esc_url}">{label}</a>'


def html_app_deep_link_block(*, link_text: str | None = None) -> str:
    url = telegram_mini_app_url()
    if url is None:
        return '📱 Откройте приложение Filmony из Telegram'
    esc_url = html.escape(url, quote=True)
    label = html.escape(link_text or _DEFAULT_LINK_LABEL)
    return f'🔗 <a href="{esc_url}">{label}</a>'


def resolve_controversy_deeplink_url(
    *,
    anchor_film_id: int | None,
    link_card_id: int | None,
) -> str | None:
    if anchor_film_id is not None:
        return telegram_mini_app_film_url(anchor_film_id)
    if link_card_id is not None:
        return telegram_mini_app_card_url(link_card_id)
    return telegram_mini_app_url()


def controversy_deeplink_html_block(
    *,
    anchor_film_id: int | None,
    link_card_id: int | None,
    link_text: str | None = None,
) -> str:
    label = link_text or 'Посмотреть все мнения'
    if anchor_film_id is not None:
        return html_film_deep_link_block(anchor_film_id, link_text=label)
    if link_card_id is not None:
        return html_card_deep_link_block(link_card_id, link_text=label)
    return html_app_deep_link_block(link_text=label)
