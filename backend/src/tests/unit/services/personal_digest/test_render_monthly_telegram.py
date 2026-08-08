"""Tests for monthly personal digest Telegram teaser rendering."""

from __future__ import annotations

from uuid import uuid4

from services.personal_digest.render_personal_digest_telegram import (
    RenderPersonalDigestTelegramService,
)
from services.profile.build_monthly_recap import (
    MonthlyRecap,
    MonthlyRecapAchievementItem,
    MonthlyRecapActorItem,
    MonthlyRecapCollectionDeltaItem,
)


def _base_recap(**overrides) -> MonthlyRecap:
    defaults = {
        'user_id': uuid4(),
        'year': 2026,
        'month': 7,
        'month_label': 'Июль 2026',
        'total_rated': 5,
        'average_rating': 8.2,
        'top_films': [],
        'new_stamps': [],
        'marathons_unlocked': [],
        'peak_activity_date': None,
        'peak_activity_count': 0,
        'genre_of_month': None,
        'genre_of_month_count': 0,
        'top_director_name': 'Дени Вильнёв',
        'top_director_count': 3,
        'top_director_kinopoisk_id': 301,
        'top_country': None,
        'top_country_count': 0,
        'new_countries_count': 0,
        'genre_breakdown': [],
        'decade_breakdown': [],
        'director_breakdown': [],
        'franchise_breakdown': [],
        'top_actor_kinopoisk_id': 401,
        'top_actor_name': 'Тимоти Шаламе',
        'top_actor_count': 2,
        'actor_breakdown': [
            MonthlyRecapActorItem(kinopoisk_id=401, label='Тимоти Шаламе', count=2),
        ],
        'collection_deltas': [],
        'achievements_unlocked': [],
        'streak_current': 3,
        'streak_best_in_period': 4,
        'vs_previous_total_rated': 2,
        'vs_previous_average_rating': 0.3,
        'dominant_mood_after': 'enjoyed',
        'dominant_company': 'alone',
        'fun_facts': [],
    }
    defaults.update(overrides)
    return MonthlyRecap(**defaults)


def test_render_monthly_teaser_includes_core_hooks() -> None:
    body = RenderPersonalDigestTelegramService.build().execute(_base_recap())
    assert 'Итоги · Июль 2026' in body
    assert '5 фильмов · ср. 8.2' in body
    assert '(+2 к июнь)' in body
    assert 'Дени Вильнёв (3)' in body
    assert 'Тимоти Шаламе (2)' in body
    assert 'лучшая серия 4 дн.' in body
    assert 'Посмотреть итоги месяца' in body


def test_render_monthly_teaser_shows_achievement_line() -> None:
    recap = _base_recap(
        achievements_unlocked=[
            MonthlyRecapAchievementItem(
                slug='horror-250',
                title='Horror 250',
                rarity_percent=12.5,
            )
        ],
    )
    body = RenderPersonalDigestTelegramService.build().execute(recap)
    assert '1 ачивки' in body


def test_render_monthly_teaser_shows_collection_delta() -> None:
    recap = _base_recap(
        collection_deltas=[
            MonthlyRecapCollectionDeltaItem(
                collection_slug='horror-250',
                title='Horror 250',
                films_rated_in_period=3,
            )
        ],
    )
    body = RenderPersonalDigestTelegramService.build().execute(recap)
    assert 'Horror 250 +3' in body
