from __future__ import annotations

from services.profile.compute_rating_contrast_insights import (
    CONTRAST_THRESHOLD,
    RatingContrastRow,
    compute_rating_contrast_insights,
)


def test_compute_rating_contrast_insights_counts_and_outliers() -> None:
    rows = [
        RatingContrastRow(
            user_rating=9.0,
            rating_kinopoisk=6.0,
            rating_imdb=7.0,
            film_id=1,
            film_title='Higher Than Both',
            card_id=101,
        ),
        RatingContrastRow(
            user_rating=4.0,
            rating_kinopoisk=8.0,
            rating_imdb=8.5,
            film_id=2,
            film_title='Lower Than Both',
            card_id=102,
        ),
        RatingContrastRow(
            user_rating=7.5,
            rating_kinopoisk=7.0,
            rating_imdb=None,
            film_id=3,
            film_title='Aligned KP',
            card_id=103,
        ),
    ]

    insights = compute_rating_contrast_insights(rows)

    assert insights.kinopoisk_compared_count == 3
    assert insights.kinopoisk_higher_count == 1
    assert insights.kinopoisk_lower_count == 1
    assert insights.imdb_compared_count == 2
    assert insights.imdb_higher_count == 1
    assert insights.imdb_lower_count == 1

    assert insights.kinopoisk_biggest_positive is not None
    assert insights.kinopoisk_biggest_positive.film_title == 'Higher Than Both'
    assert insights.kinopoisk_biggest_positive.delta == 3.0

    assert insights.kinopoisk_biggest_negative is not None
    assert insights.kinopoisk_biggest_negative.film_title == 'Lower Than Both'
    assert insights.kinopoisk_biggest_negative.delta == -4.0

    assert insights.imdb_biggest_positive is not None
    assert insights.imdb_biggest_positive.delta == 2.0

    assert insights.imdb_biggest_negative is not None
    assert insights.imdb_biggest_negative.delta == -4.5


def test_compute_rating_contrast_insights_empty_rows() -> None:
    insights = compute_rating_contrast_insights([])

    assert insights.kinopoisk_compared_count == 0
    assert insights.kinopoisk_higher_count == 0
    assert insights.kinopoisk_lower_count == 0
    assert insights.kinopoisk_biggest_positive is None
    assert insights.kinopoisk_biggest_negative is None
    assert insights.imdb_compared_count == 0
    assert insights.imdb_higher_count == 0
    assert insights.imdb_lower_count == 0
    assert insights.imdb_biggest_positive is None
    assert insights.imdb_biggest_negative is None


def test_compute_rating_contrast_insights_uses_threshold() -> None:
    row = RatingContrastRow(
        user_rating=7.0,
        rating_kinopoisk=6.5,
        rating_imdb=6.5,
        film_id=1,
        film_title='Near Match',
        card_id=1,
    )
    insights = compute_rating_contrast_insights([row])

    assert CONTRAST_THRESHOLD == 1.0
    assert insights.kinopoisk_higher_count == 0
    assert insights.kinopoisk_lower_count == 0
    assert insights.kinopoisk_biggest_positive is not None
    assert insights.kinopoisk_biggest_positive.delta == 0.5
