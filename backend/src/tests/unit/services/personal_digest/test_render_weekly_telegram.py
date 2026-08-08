"""Tests for weekly personal digest Telegram teaser rendering."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from conf import settings
from services.personal_digest.build_personal_digest import PersonalDigestDTO
from services.personal_digest.build_personal_digest_friends_section import (
    FriendDigestLine,
    FriendsDigestSection,
)
from services.personal_digest.render_personal_digest_telegram import (
    RenderPersonalDigestTelegramService,
)
from services.profile.build_monthly_recap import (
    MonthlyRecapAchievementItem,
    MonthlyRecapCollectionDeltaItem,
    MonthlyRecapFilmItem,
)


def _base_weekly_digest(**overrides) -> PersonalDigestDTO:
    user_id = uuid4()
    window_start = dt.datetime(2026, 7, 13, tzinfo=dt.UTC)
    window_end = window_start + dt.timedelta(days=7)
    defaults = {
        'user_id': user_id,
        'period': 'week',
        'period_key': '2026-W29',
        'period_label': '13 июл – 19 июл',
        'window_start': window_start,
        'window_end': window_end,
        'total_rated': 4,
        'average_rating': 8.1,
        'vs_previous_total_rated': 1,
        'vs_previous_average_rating': 0.2,
        'top_films': [
            MonthlyRecapFilmItem(
                card_id=1,
                film_id=10,
                catalog_item_id=None,
                title='Дюна 2',
                poster_url=None,
                rating=9.0,
            )
        ],
        'all_films': [],
        'top_director_name': 'Дени Вильнёв',
        'top_director_count': 2,
        'top_director_kinopoisk_id': 301,
        'top_actor_kinopoisk_id': None,
        'top_actor_name': None,
        'top_actor_count': 0,
        'director_breakdown': [],
        'actor_breakdown': [],
        'genre_breakdown': [],
        'decade_breakdown': [],
        'top_country': None,
        'top_country_count': 0,
        'new_countries_count': 0,
        'franchise_breakdown': [],
        'dominant_mood_after': 'enjoyed',
        'dominant_company': 'alone',
        'new_stamps': [],
        'marathons_unlocked': [],
        'achievements_unlocked': [],
        'collection_deltas': [],
        'peak_activity_date': None,
        'peak_activity_count': 0,
        'streak_current': 3,
        'streak_best_in_period': 3,
        'friends': FriendsDigestSection(
            telegram_lines=(
                FriendDigestLine(
                    author_user_id=uuid4(),
                    author_display='@alice',
                    profile_slug='alice',
                    line_text='«Дюна 2» (9)',
                ),
            ),
            in_app_items=(),
        ),
        'fun_facts': [],
        'controversy': None,
    }
    defaults.update(overrides)
    return PersonalDigestDTO(**defaults)


def test_render_weekly_teaser_includes_core_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')
    body = RenderPersonalDigestTelegramService.build().execute_weekly(_base_weekly_digest())
    assert 'Твоя неделя · 13 июл – 19 июл' in body
    assert '4 фильма · ср. 8.1' in body
    assert 'Дюна 2 — 9.0' in body
    assert 'Дени Вильнёв' in body
    assert 'Друзья за неделю' in body
    assert '@alice' in body
    assert 'серия 3 дн.' in body
    assert 'startapp=wd2026-W29' in body


def test_render_weekly_teaser_shows_gamification_line() -> None:
    digest = _base_weekly_digest(
        achievements_unlocked=[
            MonthlyRecapAchievementItem(slug='horror', title='Horror', rarity_percent=None)
        ],
        collection_deltas=[
            MonthlyRecapCollectionDeltaItem(
                collection_slug='lb',
                title='Letterboxd',
                films_rated_in_period=2,
            )
        ],
    )
    body = RenderPersonalDigestTelegramService.build().execute_weekly(digest)
    assert '1 ачивки' in body
