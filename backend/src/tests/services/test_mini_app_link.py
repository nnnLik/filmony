from __future__ import annotations

import pytest

from conf import settings
from services.telegram.mini_app_link import (
    telegram_mini_app_card_url,
    telegram_mini_app_feed_post_url,
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
