from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.taste_quiz.constants import SESSION_CARD_COUNT


def meaningful_rated_cards_stmt(owner_user_id) -> Select[tuple[UserCard, Film | None]]:
    return (
        select(UserCard, Film)
        .outerjoin(Film, Film.id == UserCard.film_id)
        .where(
            UserCard.user_id == owner_user_id,
            UserCard.is_planned.is_(False),
            UserCard.rating >= 1.0,
        )
    )


async def count_meaningful_rated_cards(session: AsyncSession, owner_user_id) -> int:
    stmt = (
        select(func.count())
        .select_from(UserCard)
        .where(
            UserCard.user_id == owner_user_id,
            UserCard.is_planned.is_(False),
            UserCard.rating >= 1.0,
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def list_meaningful_rated_cards(
    session: AsyncSession,
    owner_user_id,
) -> list[tuple[UserCard, Film | None]]:
    rows = (await session.execute(meaningful_rated_cards_stmt(owner_user_id))).all()
    return [(card, film) for card, film in rows]


@dataclass(frozen=True, slots=True)
class CardSnapshotFields:
    card_id: int
    snapshot_title: str
    snapshot_poster_url: str | None
    snapshot_company: str
    snapshot_mood_before: str
    snapshot_owner_rating: float
    snapshot_mood_after: str
    snapshot_watch_note: str


def build_card_snapshot(card: UserCard, film: Film | None) -> CardSnapshotFields:
    title = (card.display_title or '').strip()
    if not title and film is not None:
        title = (film.title or '').strip()
    if not title:
        title = 'Без названия'
    poster = card.display_cover_url
    if not poster and film is not None:
        poster = film.poster_url
    return CardSnapshotFields(
        card_id=card.id,
        snapshot_title=title,
        snapshot_poster_url=poster,
        snapshot_company=card.company,
        snapshot_mood_before=card.mood_before,
        snapshot_owner_rating=float(card.rating),
        snapshot_mood_after=card.mood_after,
        snapshot_watch_note=card.watch_note or '',
    )


@dataclass(frozen=True, slots=True)
class SampledCardsOutcome:
    cards: list[tuple[UserCard, Film | None]]
    reset_played: bool


def sample_session_cards(
    pool: list[tuple[UserCard, Film | None]],
    played_card_ids: list[int],
) -> SampledCardsOutcome:
    played_set = {int(x) for x in played_card_ids}
    unused = [(card, film) for card, film in pool if card.id not in played_set]
    reset_played = False
    source = unused
    if len(unused) < SESSION_CARD_COUNT:
        reset_played = True
        source = pool
    count = min(SESSION_CARD_COUNT, len(source))
    sampled = random.sample(source, count)
    return SampledCardsOutcome(cards=sampled, reset_played=reset_played)
