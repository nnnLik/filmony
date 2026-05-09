from __future__ import annotations

import pytest

from services.kinopoisk.parse_url import KinopoiskUrlParseError, parse_kinopoisk_film_id


@pytest.mark.parametrize(
    ('url', 'expected_id'),
    [
        ('https://www.kinopoisk.ru/film/6764/', 6764),
        ('https://www.kinopoisk.ru/film/6764', 6764),
        ('https://www.kinopoisk.ru/series/404900/', 404900),
        ('https://www.kinopoisk.ru/series/404900', 404900),
        ('https://m.kinopoisk.ru/series/1178445/', 1178445),
    ],
)
def test_parse_kinopoisk_film_id_accepts_film_and_series(url: str, expected_id: int) -> None:
    assert parse_kinopoisk_film_id(url) == expected_id


def test_parse_kinopoisk_film_id_rejects_non_kp_host() -> None:
    with pytest.raises(KinopoiskUrlParseError):
        parse_kinopoisk_film_id('https://example.com/film/1/')


def test_parse_kinopoisk_film_id_rejects_path_without_title_segment() -> None:
    with pytest.raises(KinopoiskUrlParseError):
        parse_kinopoisk_film_id('https://www.kinopoisk.ru/name/123/')
