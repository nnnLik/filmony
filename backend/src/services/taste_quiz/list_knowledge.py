from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_pair_progress import TasteQuizPairProgress
from models.user import User
from services.taste_quiz.scoring import compute_accuracy_pct


class TasteQuizKnowledgeDirection(StrEnum):
    TO_THEM = 'to_them'
    TO_ME = 'to_me'


@dataclass(frozen=True, slots=True)
class TasteQuizKnowledgeListItem:
    user_id: UUID
    profile_slug: str
    display_name: str | None
    avatar_url: str | None
    points_sum: float
    attempts: int
    accuracy_pct: int


@dataclass(frozen=True, slots=True)
class ListTasteQuizKnowledgeOutcome:
    items: tuple[TasteQuizKnowledgeListItem, ...]
    next_cursor: str | None


def _encode_cursor(*, accuracy_pct: int, points_sum: float, user_id: UUID) -> str:
    return f'{accuracy_pct}:{points_sum}:{user_id}'


def _decode_cursor(cursor: str) -> tuple[int, float, UUID] | None:
    parts = cursor.split(':')
    if len(parts) != 3:
        return None
    try:
        accuracy_pct = int(parts[0])
        points_sum = float(parts[1])
        user_id = UUID(parts[2])
    except (TypeError, ValueError):
        return None
    return accuracy_pct, points_sum, user_id


@dataclass
class ListTasteQuizKnowledgeService:
    """Lists knowledge edges for stats in one direction."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        viewer_user_id: UUID,
        direction: TasteQuizKnowledgeDirection,
        cursor: str | None = None,
        limit: int = 20,
    ) -> ListTasteQuizKnowledgeOutcome:
        decoded = _decode_cursor(cursor) if cursor else None
        accuracy_expr = (TasteQuizPairProgress.points_sum * 100.0) / TasteQuizPairProgress.attempts

        stmt = select(TasteQuizPairProgress, User).join(
            User,
            User.id == (
                TasteQuizPairProgress.owner_user_id
                if direction == TasteQuizKnowledgeDirection.TO_THEM
                else TasteQuizPairProgress.guesser_user_id
            ),
        )
        if direction == TasteQuizKnowledgeDirection.TO_THEM:
            stmt = stmt.where(TasteQuizPairProgress.guesser_user_id == viewer_user_id)
        else:
            stmt = stmt.where(TasteQuizPairProgress.owner_user_id == viewer_user_id)
        stmt = stmt.where(TasteQuizPairProgress.attempts > 0)

        if decoded is not None:
            last_accuracy, last_points, last_user_id = decoded
            stmt = stmt.where(
                (accuracy_expr < last_accuracy)
                | (
                    (accuracy_expr == last_accuracy)
                    & (TasteQuizPairProgress.points_sum < last_points)
                )
                | (
                    (accuracy_expr == last_accuracy)
                    & (TasteQuizPairProgress.points_sum == last_points)
                    & (User.id < last_user_id)
                )
            )

        stmt = stmt.order_by(
            desc(accuracy_expr),
            desc(TasteQuizPairProgress.points_sum),
            desc(User.id),
        ).limit(limit + 1)

        rows = (await self._session.execute(stmt)).all()
        has_more = len(rows) > limit
        page = rows[:limit]

        items: list[TasteQuizKnowledgeListItem] = []
        for progress, user in page:
            attempts = int(progress.attempts)
            points_sum = float(progress.points_sum)
            items.append(
                TasteQuizKnowledgeListItem(
                    user_id=user.id,
                    profile_slug=user.profile_slug,
                    display_name=user.display_name,
                    avatar_url=user.photo_url,
                    points_sum=points_sum,
                    attempts=attempts,
                    accuracy_pct=compute_accuracy_pct(points_sum=points_sum, attempts=attempts),
                )
            )

        next_cursor: str | None = None
        if has_more and items:
            last = items[-1]
            next_cursor = _encode_cursor(
                accuracy_pct=last.accuracy_pct,
                points_sum=last.points_sum,
                user_id=last.user_id,
            )

        return ListTasteQuizKnowledgeOutcome(items=tuple(items), next_cursor=next_cursor)
