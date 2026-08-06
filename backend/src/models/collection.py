from __future__ import annotations

import datetime as dt
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CollectionKind(StrEnum):
    evergreen = 'evergreen'
    seasonal = 'seasonal'


class Collection(Base):
    """Curated film list (evergreen or seasonal) shown in the collections catalog."""

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    kind: Mapped[CollectionKind] = mapped_column(
        SAEnum(CollectionKind, native_enum=False, length=16),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    season_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='true')
    film_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    content_updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
