"""Tests for weekly controversy Telegram HTML rendering."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from conf import settings
from services.controversy.compute_weekly_controversy import (
    ControversyPolarCard,
    WeeklyControversyBundle,
    WeeklyControversyResult,
)
from services.telegram.build_weekly_controversy_message import BuildWeeklyControversyMessageService

_WEEK_START = dt.date(2026, 7, 28)
_RECIPIENT_ID = uuid4()


def _controversy(**kwargs) -> WeeklyControversyResult:
    defaults = {
        'anchor_film_id': 1,
        'anchor_catalog_item_id': None,
        'title': 'Spicy Film',
        'spread': 8.0,
        'rater_count': 3,
        'min_rating': 2.0,
        'max_rating': 10.0,
        'link_card_id': 42,
        'film_year': 2024,
        'avg_rating': 6.0,
        'polar_low': ControversyPolarCard(card_id=10, author_display='Alice', rating=2.0),
        'polar_high': ControversyPolarCard(card_id=11, author_display='Bob', rating=10.0),
        'viewer_rating': 7.0,
    }
    defaults.update(kwargs)
    return WeeklyControversyResult(**defaults)


def _bundle(**kwargs) -> WeeklyControversyBundle:
    primary = kwargs.pop('primary', None) or _controversy()
    runner_up = kwargs.pop('runner_up', None)
    return WeeklyControversyBundle(primary=primary, runner_up=runner_up)


def _render(**kwargs):
    return BuildWeeklyControversyMessageService.build().execute(
        bundle=kwargs.pop('bundle', _bundle()),
        recipient_user_id=kwargs.pop('recipient_user_id', _RECIPIENT_ID),
        week_start=kwargs.pop('week_start', _WEEK_START),
    )


def test_message_includes_rich_html_film_deeplink_and_inline_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')

    payload = _render(
        bundle=_bundle(
            primary=_controversy(
                primary_director_name='Дени Вильнёв',
                primary_country='США',
            ),
        ),
    )

    assert '🎬 «Spicy Film» (2024)' in payload.html
    assert 'Дени Вильнёв' in payload.html
    assert 'США' in payload.html
    assert 'Ваш круг разошёлся: от 2 до 10 (ср. 6.0)' in payload.html
    assert '👎 2/10 — <b>Alice</b>' in payload.html
    assert '👍 10/10 — <b>Bob</b>' in payload.html
    assert 'Ваша оценка: <b>7/10</b>' in payload.html
    assert 'startapp=f1' in payload.html
    assert payload.reply_markup is not None
    button_url = payload.reply_markup['inline_keyboard'][0][0]['url']
    assert 'startapp=f1' in str(button_url)


def test_message_intro_is_deterministic_for_same_user_and_week() -> None:
    first = _render(recipient_user_id=_RECIPIENT_ID, week_start=_WEEK_START).html
    second = _render(recipient_user_id=_RECIPIENT_ID, week_start=_WEEK_START).html
    assert first.split('\n', 1)[0] == second.split('\n', 1)[0]


def test_message_includes_runner_up() -> None:
    runner = _controversy(title='Other Film', spread=4.0, anchor_film_id=2)
    payload = _render(bundle=_bundle(runner_up=runner))
    assert 'Ещё спорный: «Other Film» — разброс 4' in payload.html


def test_message_viewer_without_rating_prompts_to_rate() -> None:
    payload = _render(bundle=_bundle(primary=_controversy(viewer_rating=None)))
    assert 'Вы ещё не оценивали — куда бы вы поставили?' in payload.html


def test_message_escapes_title_html() -> None:
    payload = _render(bundle=_bundle(primary=_controversy(title='A & B <script>')))
    assert '🎬 «A &amp; B &lt;script&gt;»' in payload.html
    assert '<script>' not in payload.html


def test_message_catalog_uses_card_deeplink(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')
    payload = _render(
        bundle=_bundle(
            primary=_controversy(
                anchor_film_id=None,
                anchor_catalog_item_id=99,
                link_card_id=77,
            ),
        ),
    )
    assert 'startapp=c77' in payload.html
    assert 'startapp=f' not in payload.html
