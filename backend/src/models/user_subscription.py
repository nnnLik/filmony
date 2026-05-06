from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSubscription(Base):
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    follower_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    following_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint('follower_user_id <> following_user_id', name='ck_no_self_subscription'),
        UniqueConstraint('follower_user_id', 'following_user_id', name='uq_user_subscription_pair'),
    )
