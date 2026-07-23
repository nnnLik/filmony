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
from services.taste_quiz.session_mapper import TasteQuizSessionDTO, map_session


@dataclass
class AbandonTasteQuizSessionService:
    """Abandons an active session; answered cards remain in pair progress."""

    _session: AsyncSession

    class SessionNotFoundError(Exception):
        pass

    class ForbiddenError(Exception):
        pass

    class SessionNotActiveError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        guesser_user_id: UUID,
        session_id: UUID,
    ) -> TasteQuizSessionDTO:
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

        quiz_session.status = TasteQuizSessionStatus.ABANDONED
        quiz_session.finished_at = dt.datetime.now(tz=dt.UTC)
        await self._session.commit()
        await self._session.refresh(quiz_session)
        return map_session(quiz_session, session_cards_list)
