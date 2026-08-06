from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Achievement(Base):
    """Catalog row for a collection-completion achievement with rarity snapshot."""

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    collection_slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    holders_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    eligible_users_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    rarity_percent: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    rarity_calculated_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
