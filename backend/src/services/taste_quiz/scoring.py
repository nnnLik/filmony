from __future__ import annotations

from math import isfinite


class TasteQuizRatingValidationError(ValueError):
    pass


def normalize_guess_rating(value: float) -> float:
    if not isfinite(value):
        raise TasteQuizRatingValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise TasteQuizRatingValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise TasteQuizRatingValidationError('rating must be in [1, 10]')
    return snapped


def score_round(*, guess_rating: float, owner_rating: float) -> tuple[float, str]:
    delta = abs(guess_rating - owner_rating)
    if delta == 0:
        return 1.0, 'exact'
    if delta == 0.5:
        return 0.5, 'close'
    return 0.0, 'miss'


def compute_accuracy_pct(*, points_sum: float, attempts: int) -> int:
    if attempts <= 0:
        return 0
    return round(100 * points_sum / attempts)
