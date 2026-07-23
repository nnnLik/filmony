from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from models.taste_quiz_enums import TasteQuizSessionStatus
from models.taste_quiz_session import TasteQuizSession
from models.taste_quiz_session_card import TasteQuizSessionCard


@dataclass(frozen=True, slots=True)
class TasteQuizSessionCardDTO:
    session_card_id: UUID
    card_id: int
    order_index: int
    title: str
    poster_url: str | None
    company: str
    mood_before: str
    owner_rating: float | None
    mood_after: str | None
    watch_note: str | None
    guess_rating: float | None
    round_points: float | None
    verdict_key: str | None
    answered_at: dt.datetime | None


@dataclass(frozen=True, slots=True)
class TasteQuizSessionDTO:
    id: UUID
    guesser_user_id: UUID
    owner_user_id: UUID
    status: TasteQuizSessionStatus
    card_count: int
    current_index: int
    round_points: float
    cards: tuple[TasteQuizSessionCardDTO, ...]
    created_at: dt.datetime
    completed_at: dt.datetime | None


def map_session_card(card: TasteQuizSessionCard) -> TasteQuizSessionCardDTO:
    answered = card.answered_at is not None
    return TasteQuizSessionCardDTO(
        session_card_id=card.id,
        card_id=card.card_id,
        order_index=card.order_index,
        title=card.snapshot_title,
        poster_url=card.snapshot_poster_url,
        company=card.snapshot_company,
        mood_before=card.snapshot_mood_before,
        owner_rating=float(card.snapshot_owner_rating) if answered else None,
        mood_after=card.snapshot_mood_after if answered else None,
        watch_note=card.snapshot_watch_note if answered else None,
        guess_rating=float(card.guess_rating) if card.guess_rating is not None else None,
        round_points=float(card.points) if card.points is not None else None,
        verdict_key=card.verdict_key,
        answered_at=card.answered_at,
    )


def compute_current_index(cards: list[TasteQuizSessionCard]) -> int:
    for card in sorted(cards, key=lambda c: c.order_index):
        if card.answered_at is None:
            return card.order_index
    return len(cards)


def map_session(session: TasteQuizSession, cards: list[TasteQuizSessionCard]) -> TasteQuizSessionDTO:
    ordered = sorted(cards, key=lambda c: c.order_index)
    return TasteQuizSessionDTO(
        id=session.id,
        guesser_user_id=session.guesser_user_id,
        owner_user_id=session.owner_user_id,
        status=session.status,
        card_count=len(ordered),
        current_index=compute_current_index(ordered),
        round_points=float(session.round_points),
        cards=tuple(map_session_card(card) for card in ordered),
        created_at=session.started_at,
        completed_at=session.finished_at,
    )
