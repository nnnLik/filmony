"""Tests for genre_slug helper."""

from lib.genre_slug import genre_slug


def test_genre_slug_cyrillic() -> None:
    assert genre_slug('драма') == 'drama'


def test_genre_slug_spaces() -> None:
    assert genre_slug('Sci-Fi') == 'sci_fi'
