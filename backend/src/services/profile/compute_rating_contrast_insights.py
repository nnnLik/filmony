from __future__ import annotations

from dataclasses import dataclass

CONTRAST_THRESHOLD = 1.0


@dataclass(frozen=True, slots=True)
class RatingContrastRow:
    user_rating: float
    rating_kinopoisk: float | None
    rating_imdb: float | None
    film_id: int
    film_title: str
    card_id: int


@dataclass(frozen=True, slots=True)
class RatingContrastOutlier:
    card_id: int
    film_id: int
    film_title: str
    user_rating: float
    external_rating: float
    delta: float


@dataclass(frozen=True, slots=True)
class RatingContrastInsights:
    kinopoisk_compared_count: int
    kinopoisk_higher_count: int
    kinopoisk_lower_count: int
    kinopoisk_biggest_positive: RatingContrastOutlier | None
    kinopoisk_biggest_negative: RatingContrastOutlier | None
    imdb_compared_count: int
    imdb_higher_count: int
    imdb_lower_count: int
    imdb_biggest_positive: RatingContrastOutlier | None
    imdb_biggest_negative: RatingContrastOutlier | None


def _outlier(row: RatingContrastRow, external_rating: float, delta: float) -> RatingContrastOutlier:
    return RatingContrastOutlier(
        card_id=row.card_id,
        film_id=row.film_id,
        film_title=row.film_title,
        user_rating=row.user_rating,
        external_rating=external_rating,
        delta=round(delta, 1),
    )


def _analyze_source(
    rows: list[RatingContrastRow],
    *,
    get_external_rating,
) -> tuple[int, int, int, RatingContrastOutlier | None, RatingContrastOutlier | None]:
    compared = 0
    higher = 0
    lower = 0
    biggest_positive: RatingContrastOutlier | None = None
    biggest_negative: RatingContrastOutlier | None = None

    for row in rows:
        external_rating = get_external_rating(row)
        if external_rating is None:
            continue
        compared += 1
        delta = row.user_rating - external_rating
        if delta >= CONTRAST_THRESHOLD:
            higher += 1
        elif delta <= -CONTRAST_THRESHOLD:
            lower += 1
        outlier = _outlier(row, external_rating, delta)
        if delta > 0 and (biggest_positive is None or delta > biggest_positive.delta):
            biggest_positive = outlier
        if delta < 0 and (biggest_negative is None or delta < biggest_negative.delta):
            biggest_negative = outlier

    return compared, higher, lower, biggest_positive, biggest_negative


def compute_rating_contrast_insights(rows: list[RatingContrastRow]) -> RatingContrastInsights:
    kp_compared, kp_higher, kp_lower, kp_pos, kp_neg = _analyze_source(
        rows,
        get_external_rating=lambda row: row.rating_kinopoisk,
    )
    imdb_compared, imdb_higher, imdb_lower, imdb_pos, imdb_neg = _analyze_source(
        rows,
        get_external_rating=lambda row: row.rating_imdb,
    )
    return RatingContrastInsights(
        kinopoisk_compared_count=kp_compared,
        kinopoisk_higher_count=kp_higher,
        kinopoisk_lower_count=kp_lower,
        kinopoisk_biggest_positive=kp_pos,
        kinopoisk_biggest_negative=kp_neg,
        imdb_compared_count=imdb_compared,
        imdb_higher_count=imdb_higher,
        imdb_lower_count=imdb_lower,
        imdb_biggest_positive=imdb_pos,
        imdb_biggest_negative=imdb_neg,
    )


__all__ = (
    'CONTRAST_THRESHOLD',
    'RatingContrastInsights',
    'RatingContrastOutlier',
    'RatingContrastRow',
    'compute_rating_contrast_insights',
)
