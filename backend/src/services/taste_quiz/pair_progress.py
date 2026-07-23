from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_pair_progress import TasteQuizPairProgress
from services.taste_quiz.scoring import compute_accuracy_pct


async def get_or_create_pair_progress(
    session: AsyncSession,
    *,
    guesser_user_id: UUID,
    owner_user_id: UUID,
) -> TasteQuizPairProgress:
    row = (
        await session.execute(
            select(TasteQuizPairProgress).where(
                TasteQuizPairProgress.guesser_user_id == guesser_user_id,
                TasteQuizPairProgress.owner_user_id == owner_user_id,
            )
        )
    ).scalar_one_or_none()
    if row is not None:
        return row
    progress = TasteQuizPairProgress(
        guesser_user_id=guesser_user_id,
        owner_user_id=owner_user_id,
        points_sum=0.0,
        attempts=0,
        played_card_ids=[],
    )
    session.add(progress)
    await session.flush()
    return progress


def apply_answer_to_pair_progress(
    progress: TasteQuizPairProgress,
    *,
    card_id: int,
    round_points: float,
) -> None:
    progress.attempts += 1
    progress.points_sum = float(progress.points_sum) + round_points
    played = list(progress.played_card_ids or [])
    if card_id not in played:
        played.append(card_id)
    progress.played_card_ids = played


def pair_progress_snapshot(progress: TasteQuizPairProgress) -> dict[str, float | int]:
    attempts = int(progress.attempts)
    points_sum = float(progress.points_sum)
    return {
        'points_sum': points_sum,
        'attempts': attempts,
        'accuracy_pct': compute_accuracy_pct(points_sum=points_sum, attempts=attempts),
    }
