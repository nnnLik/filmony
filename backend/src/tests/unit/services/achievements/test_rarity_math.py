"""Unit tests for achievement rarity math."""

from __future__ import annotations

from services.achievements.rarity_math import compute_rarity_percent


def test_compute_rarity_percent_normal_case() -> None:
    assert compute_rarity_percent(holders_count=2, eligible_users_count=8) == 25.0


def test_compute_rarity_percent_zero_eligible() -> None:
    assert compute_rarity_percent(holders_count=0, eligible_users_count=0) is None


def test_compute_rarity_percent_rounds_to_four_decimals() -> None:
    assert compute_rarity_percent(holders_count=1, eligible_users_count=3) == 33.3333
