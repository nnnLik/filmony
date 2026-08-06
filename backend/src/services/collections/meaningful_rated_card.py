from __future__ import annotations

from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement

from models.user_card import UserCard


def meaningful_rated_card_criteria(
    *,
    user_id: UUID | None = None,
) -> tuple[ColumnElement[bool], ...]:
    """Shared SQLAlchemy filters for a user's meaningful rated film-backed card."""
    criteria: list[ColumnElement[bool]] = [
        UserCard.is_planned.is_(False),
        UserCard.rating >= 1.0,
        UserCard.film_id.is_not(None),
    ]
    if user_id is not None:
        criteria.append(UserCard.user_id == user_id)
    return tuple(criteria)


def is_meaningful_rated_card(card: UserCard) -> bool:
    """Return True when the card counts toward collection progress."""
    return card.film_id is not None and not card.is_planned and float(card.rating) >= 1.0
