"""Unit tests for personal digest fun facts engine."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from services.personal_digest.build_personal_digest_fun_facts import (
    BuildPersonalDigestFunFactsService,
    DigestBuildContext,
)


def _ctx(
    *,
    user_id: UUID | None = None,
    period: str = 'week',
    period_key: str = '2026-W19',
    total_rated: int = 10,
    ratings: tuple[float, ...] = (8.0, 9.0, 7.0),
    genre_breakdown: tuple[tuple[str, int], ...] = (),
    decade_breakdown: tuple[tuple[int, int], ...] = (),
    marathons_unlocked: tuple[str, ...] = (),
    collection_deltas: tuple[tuple[str, str, int, int | None], ...] = (),
    new_countries_count: int = 0,
    streak_best_in_period: int = 0,
) -> DigestBuildContext:
    return DigestBuildContext(
        user_id=user_id or uuid4(),
        period=period,  # type: ignore[arg-type]
        period_key=period_key,
        total_rated=total_rated,
        ratings=ratings,
        genre_breakdown=genre_breakdown,
        decade_breakdown=decade_breakdown,
        marathons_unlocked=marathons_unlocked,
        collection_deltas=collection_deltas,
        new_countries_count=new_countries_count,
        streak_best_in_period=streak_best_in_period,
    )


def test_genre_dominance_rule_fires_at_sixty_percent() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            total_rated=10,
            genre_breakdown=(('драма', 6), ('комедия', 2)),
        )
    )
    assert any('драма — 60% недели' in fact for fact in facts)


def test_rating_all_high_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(ratings=(8.0, 9.0, 10.0)))
    assert 'Без разочарований' in facts


def test_rating_wide_spread_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(ratings=(3.0, 9.0)))
    assert any('Разброс вкуса 3–9' in fact for fact in facts)


def test_era_skew_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            total_rated=10,
            decade_breakdown=((1990, 5), (2000, 3)),
        )
    )
    assert any('Одержим 1990-ми' in fact for fact in facts)


def test_collection_sprint_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            collection_deltas=(('oscars', 'Оскар', 5, 20),),
        )
    )
    assert any('Прокачал Оскар' in fact for fact in facts)


def test_marathon_complete_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(marathons_unlocked=('Нолан',)))
    assert any('Закрыл марафон Нолан' in fact for fact in facts)


def test_new_country_burst_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(new_countries_count=3))
    assert '3 новых стран' in facts


def test_streak_record_rule() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(streak_best_in_period=7))
    assert 'Рекорд серии: 7' in facts


def test_microfun_fallback_pads_when_sparse() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(ratings=(7.0, 7.5), total_rated=2))
    assert len(facts) >= 2
    assert all(isinstance(fact, str) and fact for fact in facts)


def test_weekly_caps_at_three_facts() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            period='week',
            ratings=(8.0, 9.0, 10.0),
            genre_breakdown=(('драма', 8),),
            total_rated=10,
            decade_breakdown=((1990, 6),),
            marathons_unlocked=('Нолан',),
            new_countries_count=4,
            streak_best_in_period=8,
            collection_deltas=(('oscars', 'Оскар', 5, 20),),
        )
    )
    assert len(facts) <= 3


def test_monthly_caps_at_five_facts() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            period='month',
            period_key='2026-05',
            ratings=(8.0, 9.0, 10.0),
            genre_breakdown=(('драма', 8),),
            total_rated=10,
            decade_breakdown=((1990, 6),),
            marathons_unlocked=('Нолан',),
            new_countries_count=4,
            streak_best_in_period=8,
            collection_deltas=(('oscars', 'Оскар', 5, 20),),
        )
    )
    assert len(facts) <= 5


def test_monthly_scope_label_in_genre_dominance() -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(
        _ctx(
            period='month',
            period_key='2026-05',
            total_rated=5,
            genre_breakdown=(('ужасы', 3),),
        )
    )
    assert any('ужасы — 60% месяца' in fact for fact in facts)


def test_deterministic_tie_break_for_same_user_and_period() -> None:
    user_id = UUID('00000000-0000-0000-0000-000000000001')
    svc = BuildPersonalDigestFunFactsService.build()
    ctx = _ctx(
        user_id=user_id,
        period='week',
        period_key='2026-W20',
        ratings=(8.0, 9.0, 10.0),
        genre_breakdown=(('драма', 8),),
        total_rated=10,
        decade_breakdown=((1990, 6),),
        marathons_unlocked=('Нолан',),
        new_countries_count=4,
        streak_best_in_period=8,
        collection_deltas=(('oscars', 'Оскар', 5, 20),),
    )
    first = svc.execute(ctx)
    second = svc.execute(ctx)
    assert first == second


@pytest.mark.parametrize(
    ('ratings', 'expected_present'),
    [
        ((7.9, 8.0), False),
        ((8.0, 8.5), True),
    ],
)
def test_rating_all_high_boundary(
    ratings: tuple[float, ...],
    expected_present: bool,
) -> None:
    svc = BuildPersonalDigestFunFactsService.build()
    facts = svc.execute(_ctx(ratings=ratings))
    assert ('Без разочарований' in facts) is expected_present
