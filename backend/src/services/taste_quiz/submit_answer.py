from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_enums import TasteQuizSessionStatus
from models.taste_quiz_session import TasteQuizSession
from models.taste_quiz_session_card import TasteQuizSessionCard
from services.taste_quiz.pair_progress import (
    apply_answer_to_pair_progress,
    get_or_create_pair_progress,
    pair_progress_snapshot,
)
from services.taste_quiz.scoring import (
    TasteQuizRatingValidationError,
    normalize_guess_rating,
    score_round,
)
from services.taste_quiz.session_mapper import (
    TasteQuizSessionCardDTO,
    TasteQuizSessionDTO,
    compute_current_index,
    map_session,
    map_session_card,
)


@dataclass(frozen=True, slots=True)
class SubmitTasteQuizAnswerOutcome:
    card: TasteQuizSessionCardDTO
    session: TasteQuizSessionDTO
    pair_progress: dict[str, float | int]
    session_completed: bool


@dataclass
class SubmitTasteQuizAnswerService:
    """Scores one guess, updates edge progress, and may complete the session."""

    _session: AsyncSession

    class SessionNotFoundError(Exception):
        pass

    class ForbiddenError(Exception):
        pass

    class SessionNotActiveError(Exception):
        pass

    class CardNotFoundError(Exception):
        pass

    class AlreadyAnsweredError(Exception):
        pass

    class WrongCardOrderError(Exception):
        pass

    class InvalidRatingError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        guesser_user_id: UUID,
        session_id: UUID,
        session_card_id: UUID,
        guess_rating: float,
    ) -> SubmitTasteQuizAnswerOutcome:
        try:
            normalized_guess = normalize_guess_rating(guess_rating)
        except TasteQuizRatingValidationError as exc:
            raise self.InvalidRatingError(str(exc)) from exc

        quiz_session = await self._session.get(TasteQuizSession, session_id)
        if quiz_session is None:
            raise self.SessionNotFoundError
        if quiz_session.guesser_user_id != guesser_user_id:
            raise self.ForbiddenError
        if quiz_session.status != TasteQuizSessionStatus.ACTIVE:
            raise self.SessionNotActiveError

        session_cards = (
            await self._session.execute(
                select(TasteQuizSessionCard)
                .where(TasteQuizSessionCard.session_id == session_id)
                .order_by(TasteQuizSessionCard.order_index)
            )
        ).scalars().all()
        session_cards_list = list(session_cards)

        session_card = next((c for c in session_cards_list if c.id == session_card_id), None)
        if session_card is None:
            raise self.CardNotFoundError
        if session_card.answered_at is not None:
            raise self.AlreadyAnsweredError

        current_index = compute_current_index(session_cards_list)
        if session_card.order_index != current_index:
            raise self.WrongCardOrderError

        round_points, verdict_key = score_round(
            guess_rating=normalized_guess,
            owner_rating=float(session_card.snapshot_owner_rating),
        )
        now = dt.datetime.now(tz=dt.UTC)
        session_card.guess_rating = normalized_guess
        session_card.points = round_points
        session_card.verdict_key = verdict_key
        session_card.answered_at = now
        quiz_session.round_points = float(quiz_session.round_points) + round_points

        progress = await get_or_create_pair_progress(
            self._session,
            guesser_user_id=guesser_user_id,
            owner_user_id=quiz_session.owner_user_id,
        )
        apply_answer_to_pair_progress(
            progress,
            card_id=session_card.card_id,
            round_points=round_points,
        )

        session_completed = all(card.answered_at is not None for card in session_cards_list)
        if session_completed:
            quiz_session.status = TasteQuizSessionStatus.COMPLETED
            quiz_session.finished_at = now

        await self._session.commit()
        await self._session.refresh(quiz_session)
        await self._session.refresh(session_card)
        await self._session.refresh(progress)

        return SubmitTasteQuizAnswerOutcome(
            card=map_session_card(session_card),
            session=map_session(quiz_session, session_cards_list),
            pair_progress=pair_progress_snapshot(progress),
            session_completed=session_completed,
        )
