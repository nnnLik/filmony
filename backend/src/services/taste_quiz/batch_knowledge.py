from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_pair_progress import TasteQuizPairProgress
from services.taste_quiz.scoring import compute_accuracy_pct


@dataclass(frozen=True, slots=True)
class TasteQuizKnowledgeBatchItem:
    attempts: int
    accuracy_pct: int
    points_sum: float


@dataclass
class BatchTasteQuizKnowledgeService:
    """Returns knowledge edges for comment enrichment."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        owner_user_id: UUID,
        guesser_user_ids: list[UUID],
    ) -> dict[UUID, TasteQuizKnowledgeBatchItem]:
        unique_ids = list(dict.fromkeys(guesser_user_ids))
        if not unique_ids:
            return {}

        rows = (
            await self._session.execute(
                select(TasteQuizPairProgress).where(
                    TasteQuizPairProgress.owner_user_id == owner_user_id,
                    TasteQuizPairProgress.guesser_user_id.in_(unique_ids),
                    TasteQuizPairProgress.attempts > 0,
                )
            )
        ).scalars().all()

        out: dict[UUID, TasteQuizKnowledgeBatchItem] = {}
        for progress in rows:
            attempts = int(progress.attempts)
            points_sum = float(progress.points_sum)
            out[progress.guesser_user_id] = TasteQuizKnowledgeBatchItem(
                attempts=attempts,
                accuracy_pct=compute_accuracy_pct(points_sum=points_sum, attempts=attempts),
                points_sum=points_sum,
            )
        return out
