from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CatalogItem(Base):
    """Maps an external canonical title (Kinopoisk, future providers) to persisted rows."""

    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    film_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint('provider', 'external_id', name='uq_catalog_item_provider_external'),
    )
