"""Unit tests for universal release parsing from Film.year vs Game.released."""

from __future__ import annotations

import pytest

from services.cards.card_catalog_release_fields import (
    split_game_released_iso,
    universal_release_year_date,
)


@pytest.mark.parametrize(
    ('raw', 'expected_iso', 'expected_year'),
    [
        (None, None, None),
        ('', None, None),
        ('   ', None, None),
        ('2015-05-18', '2015-05-18', 2015),
        ('2015-05-18T00:00:00', '2015-05-18', 2015),
        ('2013', None, 2013),
        ('not-a-date', None, None),
        ('2015-13-40', None, None),
    ],
)
def test_split_game_released_iso(
    raw: str | None,
    expected_iso: str | None,
    expected_year: int | None,
) -> None:
    iso, y = split_game_released_iso(raw)
    assert iso == expected_iso
    assert y == expected_year


def test_universal_release_prefers_film_year() -> None:
    y, d = universal_release_year_date(film_year=2014, game_released='2015-05-18')
    assert y == 2014
    assert d is None


def test_universal_release_falls_back_to_game() -> None:
    y, d = universal_release_year_date(film_year=None, game_released='2015-05-18')
    assert y == 2015
    assert d == '2015-05-18'
