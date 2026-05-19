from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

DEFAULT_USER_CARD_CATEGORY_NAME = 'Фильмы'


class UserCardCategory(Base):
    """User-owned shelf/category; organizes cards independently of catalog matching."""

    __tablename__ = 'user_card_category'

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_card_category_user_name'),
        Index('ix_user_card_category_user_id_name', 'user_id', 'name'),
    )
