from __future__ import annotations


def compute_rarity_percent(*, holders_count: int, eligible_users_count: int) -> float | None:
    """Return holder share among eligible raters, or None when denominator is zero."""
    if eligible_users_count <= 0:
        return None
    return round((holders_count / eligible_users_count) * 100.0, 4)
