from __future__ import annotations

import pytest

from conf import settings
from services.telegram.mini_app_link import (
    resolve_controversy_deeplink_url,
    telegram_mini_app_card_url,
    telegram_mini_app_feed_post_url,
    telegram_mini_app_film_url,
)


def test_notification_link_uses_app_segment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'mybot')
    assert telegram_mini_app_card_url(11) == 'https://t.me/mybot/app?startapp=c11'


def test_strips_at(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', '@mybot')
    assert telegram_mini_app_card_url(1) == 'https://t.me/mybot/app?startapp=c1'


def test_missing_username(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', None)
    assert telegram_mini_app_card_url(1) is None


def test_feed_post_deep_link(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'mybot')
    assert telegram_mini_app_feed_post_url(42) == 'https://t.me/mybot/app?startapp=p42'


def test_film_deep_link(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'mybot')
    assert telegram_mini_app_film_url(7) == 'https://t.me/mybot/app?startapp=f7'


def test_recap_deep_link(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.telegram.mini_app_link import telegram_mini_app_recap_url

    monkeypatch.setattr(settings.telegram, 'bot_username', 'mybot')
    assert (
        telegram_mini_app_recap_url(year=2026, month=8) == 'https://t.me/mybot/app?startapp=r20268'
    )


def test_resolve_controversy_deeplink_prefers_film(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'mybot')
    url = resolve_controversy_deeplink_url(anchor_film_id=3, link_card_id=9)
    assert url == 'https://t.me/mybot/app?startapp=f3'
