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
from services.taste_quiz.card_pool import (
    build_card_snapshot,
    list_meaningful_rated_cards,
    sample_session_cards,
)
from services.taste_quiz.check_can_play import CheckTasteQuizCanPlayService
from services.taste_quiz.pair_progress import get_or_create_pair_progress
from services.taste_quiz.session_mapper import TasteQuizSessionDTO, map_session


@dataclass
class CreateTasteQuizSessionService:
    """Creates a taste-quiz session with sampled cards and immutable snapshots."""

    _session: AsyncSession
    _can_play_service: CheckTasteQuizCanPlayService

    class GateError(Exception):
        pass

    class NotFollowingError(Exception):
        pass

    class ActiveSessionExistsError(Exception):
        session_id: UUID

        def __init__(self, session_id: UUID) -> None:
            self.session_id = session_id
            super().__init__('active session exists')

    class OwnerNotFoundError(Exception):
        pass

    class SelfPlayError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _can_play_service=CheckTasteQuizCanPlayService.build(session),
        )

    async def execute(
        self,
        *,
        guesser_user_id: UUID,
        owner_user_id: UUID,
        invite_token: str | None = None,
    ) -> TasteQuizSessionDTO:
        try:
            can_play_outcome = await self._can_play_service.execute(
                guesser_user_id=guesser_user_id,
                owner_user_id=owner_user_id,
                invite_token=invite_token,
            )
        except CheckTasteQuizCanPlayService.SelfPlayError:
            raise self.SelfPlayError from None
        except CheckTasteQuizCanPlayService.OwnerNotFoundError:
            raise self.OwnerNotFoundError from None

        if can_play_outcome.reason == 'owner_insufficient_cards':
            raise self.GateError
        if can_play_outcome.reason == 'not_following':
            raise self.NotFollowingError
        if can_play_outcome.active_session_id is not None:
            raise self.ActiveSessionExistsError(can_play_outcome.active_session_id)

        pool = await list_meaningful_rated_cards(self._session, owner_user_id)
        progress = await get_or_create_pair_progress(
            self._session,
            guesser_user_id=guesser_user_id,
            owner_user_id=owner_user_id,
        )
        sampled = sample_session_cards(pool, list(progress.played_card_ids or []))
        if sampled.reset_played:
            progress.played_card_ids = []

        quiz_session = TasteQuizSession(
            guesser_user_id=guesser_user_id,
            owner_user_id=owner_user_id,
            status=TasteQuizSessionStatus.ACTIVE,
            round_points=0.0,
            started_at=dt.datetime.now(tz=dt.UTC),
        )
        self._session.add(quiz_session)
        await self._session.flush()

        session_cards: list[TasteQuizSessionCard] = []
        for order_index, (card, film) in enumerate(sampled.cards):
            snapshot = build_card_snapshot(card, film)
            session_card = TasteQuizSessionCard(
                session_id=quiz_session.id,
                card_id=snapshot.card_id,
                order_index=order_index,
                snapshot_title=snapshot.snapshot_title,
                snapshot_poster_url=snapshot.snapshot_poster_url,
                snapshot_company=snapshot.snapshot_company,
                snapshot_mood_before=snapshot.snapshot_mood_before,
                snapshot_owner_rating=snapshot.snapshot_owner_rating,
                snapshot_mood_after=snapshot.snapshot_mood_after,
                snapshot_watch_note=snapshot.snapshot_watch_note,
            )
            self._session.add(session_card)
            session_cards.append(session_card)

        await self._session.commit()
        for card in session_cards:
            await self._session.refresh(card)
        await self._session.refresh(quiz_session)
        return map_session(quiz_session, session_cards)
