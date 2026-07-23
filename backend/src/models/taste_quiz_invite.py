from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TasteQuizInvite(Base):
    """Owner invite token for taste-quiz deep link."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
