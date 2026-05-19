from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Game(Base):
    """RAWG game row: normalized query fields plus full list/detail JSON snapshots."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    rawg_id: Mapped[int] = mapped_column(Integer, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    name_original: Mapped[str | None] = mapped_column(String(512), nullable=True)

    released: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tba: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    background_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    background_image_additional: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_top: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ratings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metacritic: Mapped[int | None] = mapped_column(Integer, nullable=True)

    platforms_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    esrb_rating_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    ratings_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    added_by_status_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    metacritic_platforms_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    reactions_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    alternative_names_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    raw_search_snapshot: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    raw_detail_snapshot: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    search_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    detail_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint('rawg_id', name='uq_game_rawg_id'),)
