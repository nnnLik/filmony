from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, Field


class TasteQuizCanPlayResponse(BaseModel):
    can_play: bool
    reason: str | None
    owner_rated_count: int
    requires_follow: bool
    guesser_follows_owner: bool
    active_session_id: UUID | None
    gate_min_rated_cards: int


class TasteQuizCreateSessionRequest(BaseModel):
    owner_id: UUID
    invite_token: str | None = None


class TasteQuizSessionCardResponse(BaseModel):
    session_card_id: UUID
    card_id: int
    order_index: int
    title: str
    poster_url: str | None
    company: str
    mood_before: str
    owner_rating: float | None = None
    mood_after: str | None = None
    watch_note: str | None = None
    guess_rating: float | None = None
    round_points: float | None = None
    verdict_key: str | None = None
    answered_at: dt.datetime | None = None


class TasteQuizSessionResponse(BaseModel):
    id: UUID
    guesser_user_id: UUID
    owner_user_id: UUID
    status: str
    card_count: int
    current_index: int
    round_points: float
    cards: list[TasteQuizSessionCardResponse]
    created_at: dt.datetime
    completed_at: dt.datetime | None = None


class TasteQuizSubmitAnswerRequest(BaseModel):
    session_card_id: UUID
    guess_rating: float = Field(ge=1.0, le=10.0)


class TasteQuizPairProgressResponse(BaseModel):
    points_sum: float
    attempts: int
    accuracy_pct: int


class TasteQuizSubmitAnswerResponse(BaseModel):
    card: TasteQuizSessionCardResponse
    session: TasteQuizSessionResponse
    pair_progress: TasteQuizPairProgressResponse
    session_completed: bool


class TasteQuizKnowledgeItemResponse(BaseModel):
    user_id: UUID
    profile_slug: str
    display_name: str | None
    avatar_url: str | None
    points_sum: float
    attempts: int
    accuracy_pct: int


class TasteQuizKnowledgeListResponse(BaseModel):
    items: list[TasteQuizKnowledgeItemResponse]
    next_cursor: str | None = None


class TasteQuizKnowledgeBatchRequest(BaseModel):
    owner_id: UUID
    guesser_user_ids: list[UUID]


class TasteQuizKnowledgeBatchItemResponse(BaseModel):
    attempts: int
    accuracy_pct: int
    points_sum: float


class TasteQuizKnowledgeBatchResponse(BaseModel):
    items: dict[str, TasteQuizKnowledgeBatchItemResponse]


class TasteQuizCreateInviteResponse(BaseModel):
    invite_token: str
    share_url: str | None
    telegram_share_text: str


class TasteQuizInviteOwnerSnippetResponse(BaseModel):
    user_id: UUID
    profile_slug: str
    display_name: str | None
    avatar_url: str | None


class TasteQuizResolveInviteResponse(BaseModel):
    owner: TasteQuizInviteOwnerSnippetResponse
    invite_token: str
    share_url: str | None
    can_play: bool
    reason: str | None
    owner_rated_count: int
    gate_min_rated_cards: int
    expired: bool
