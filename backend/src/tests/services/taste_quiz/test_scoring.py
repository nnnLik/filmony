from __future__ import annotations

import pytest

from services.taste_quiz.scoring import (
    TasteQuizRatingValidationError,
    compute_accuracy_pct,
    normalize_guess_rating,
    score_round,
)


@pytest.mark.parametrize(
    ('guess', 'owner', 'points', 'verdict'),
    [
        (8.0, 8.0, 1.0, 'exact'),
        (8.5, 8.0, 0.5, 'close'),
        (8.0, 8.5, 0.5, 'close'),
        (7.0, 8.0, 0.0, 'miss'),
        (9.0, 8.0, 0.0, 'miss'),
    ],
)
def test_score_round(guess: float, owner: float, points: float, verdict: str) -> None:
    assert score_round(guess_rating=guess, owner_rating=owner) == (points, verdict)


def test_compute_accuracy_pct_rounds_to_int() -> None:
    assert compute_accuracy_pct(points_sum=11.0, attempts=20) == 55
    assert compute_accuracy_pct(points_sum=0.0, attempts=0) == 0


def test_normalize_guess_rating_accepts_half_steps() -> None:
    assert normalize_guess_rating(7.5) == 7.5


def test_normalize_guess_rating_rejects_bad_step() -> None:
    with pytest.raises(TasteQuizRatingValidationError, match=r'0.5 step'):
        normalize_guess_rating(7.3)


def test_normalize_guess_rating_rejects_out_of_range() -> None:
    with pytest.raises(TasteQuizRatingValidationError, match='\\[1, 10\\]'):
        normalize_guess_rating(10.5)
