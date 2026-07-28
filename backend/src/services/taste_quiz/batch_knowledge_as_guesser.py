from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.taste_quiz_pair_progress import TasteQuizPairProgress
from services.taste_quiz.batch_knowledge import TasteQuizKnowledgeBatchItem
from services.taste_quiz.scoring import compute_accuracy_pct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class BatchTasteQuizKnowledgeAsGuesserService:
    """Returns how well one guesser knows many owners for comment enrichment."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        guesser_user_id: UUID,
        owner_user_ids: list[UUID],
    ) -> dict[UUID, TasteQuizKnowledgeBatchItem]:
        unique_ids = [
            owner_id for owner_id in dict.fromkeys(owner_user_ids) if owner_id != guesser_user_id
        ]
        if not unique_ids:
            return {}

        rows = (
            (
                await self._session.execute(
                    select(TasteQuizPairProgress).where(
                        TasteQuizPairProgress.guesser_user_id == guesser_user_id,
                        TasteQuizPairProgress.owner_user_id.in_(unique_ids),
                        TasteQuizPairProgress.attempts > 0,
                    )
                )
            )
            .scalars()
            .all()
        )

        out: dict[UUID, TasteQuizKnowledgeBatchItem] = {}
        for progress in rows:
            attempts = int(progress.attempts)
            points_sum = float(progress.points_sum)
            out[progress.owner_user_id] = TasteQuizKnowledgeBatchItem(
                attempts=attempts,
                accuracy_pct=compute_accuracy_pct(points_sum=points_sum, attempts=attempts),
                points_sum=points_sum,
            )
        return out
