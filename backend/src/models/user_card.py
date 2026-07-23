from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    false,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .catalog_item import CatalogProvider


class UserCard(Base):
    """End-user-owned card (film/catalog/manual)."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    film_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    catalog_item_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('catalog_item.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        'user_card_category_id',
        Integer,
        ForeignKey('user_card_category.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    provider: Mapped[CatalogProvider] = mapped_column(
        SAEnum(CatalogProvider, native_enum=False, length=64),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_cover_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    display_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    company: Mapped[str] = mapped_column(String(32), nullable=False)
    mood_before: Mapped[str] = mapped_column(String(32), nullable=False)
    mood_after: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    watch_note: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        default='',
        server_default=text("''"),
    )
    is_planned: Mapped[bool] = mapped_column(
        Boolean(),
        server_default=false(),
        nullable=False,
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean(),
        server_default=false(),
        nullable=False,
    )
    favorite_marked_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    audio_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    __table_args__ = (
        Index(
            'uq_user_card_user_catalog_item_id_partial',
            'user_id',
            'catalog_item_id',
            unique=True,
            postgresql_where=text('catalog_item_id IS NOT NULL'),
        ),
        Index(
            'uq_user_card_user_film_id_partial',
            'user_id',
            'film_id',
            unique=True,
            postgresql_where=text('film_id IS NOT NULL'),
        ),
        Index(
            'uq_user_card_user_provider_external_kinopoisk_partial',
            'user_id',
            'provider',
            'external_id',
            unique=True,
            postgresql_where=text("provider = 'kinopoisk' AND external_id IS NOT NULL"),
        ),
        Index(
            'uq_user_card_user_provider_external_youtube_partial',
            'user_id',
            'provider',
            'external_id',
            unique=True,
            postgresql_where=text("provider = 'youtube' AND external_id IS NOT NULL"),
        ),
        Index(
            'ix_user_card_user_id_created_at_id',
            'user_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
        Index(
            'ix_user_card_created_at_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
        Index(
            'ix_user_card_updated_at_id',
            'updated_at',
            'id',
            postgresql_ops={'updated_at': 'DESC', 'id': 'DESC'},
        ),
        Index(
            'ix_user_card_user_favorites_order',
            'user_id',
            'favorite_marked_at',
            'id',
            postgresql_ops={'favorite_marked_at': 'DESC NULLS LAST', 'id': 'DESC'},
            postgresql_where=text('is_favorite IS TRUE'),
        ),
    )
