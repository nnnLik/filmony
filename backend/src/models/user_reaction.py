from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserReaction(Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    reaction_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('reaction_type.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    target_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'target_kind',
            'target_id',
            'reaction_type_id',
            name='uq_user_reaction_user_target_kind_type',
        ),
        Index('ix_user_reaction_target', 'target_kind', 'target_id'),
        Index('ix_user_reaction_user_target_kind', 'user_id', 'target_kind', 'target_id'),
        Index(
            'ix_user_reaction_target_kind_type_id',
            'target_kind',
            'target_id',
            'reaction_type_id',
            'id',
            postgresql_ops={'id': 'DESC'},
        ),
    )
