"""Tests for weekly controversy Telegram HTML rendering."""

from __future__ import annotations

import pytest

from conf import settings
from services.controversy.compute_weekly_controversy import WeeklyControversyResult
from services.telegram.build_weekly_controversy_message import BuildWeeklyControversyMessageService


def _controversy(**kwargs) -> WeeklyControversyResult:
    defaults = {
        'anchor_film_id': 1,
        'anchor_catalog_item_id': None,
        'title': 'Spicy Film',
        'spread': 8.0,
        'rater_count': 3,
        'min_rating': 2.0,
        'max_rating': 10.0,
        'link_card_id': None,
    }
    defaults.update(kwargs)
    return WeeklyControversyResult(**defaults)


def test_message_includes_rich_html_and_card_deeplink(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')

    body = BuildWeeklyControversyMessageService.build().execute(
        controversy=_controversy(link_card_id=42),
    )

    assert '⚡ <b>Спорный тайтл недели</b>' in body
    assert '🎬 «Spicy Film»' in body
    assert '📊 Оценки от 2 до 10 · разброс 8 · 3 чел.' in body
    assert 'startapp=c42' in body
    assert 'Посмотреть мнения подписок' in body
    assert body.index('⚡') < body.index('🎬') < body.index('📊') < body.index('🔗')


def test_message_escapes_title_html() -> None:
    body = BuildWeeklyControversyMessageService.build().execute(
        controversy=_controversy(title='A & B <script>'),
    )

    assert '🎬 «A &amp; B &lt;script&gt;»' in body
    assert '<script>' not in body


def test_message_falls_back_to_app_link_when_no_card(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')

    body = BuildWeeklyControversyMessageService.build().execute(
        controversy=_controversy(link_card_id=None),
    )

    assert 'startapp=c' not in body
    assert 'https://t.me/stubfilmony_bot/app' in body
    assert 'Посмотреть мнения подписок' in body
