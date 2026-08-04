from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Film(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kinopoisk_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    countries: Mapped[list[str]] = mapped_column(JSON, default=list)
    primary_director_kinopoisk_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    primary_director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_director_poster_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    primary_director_tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    franchise_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    imdb_id: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    tmdb_detail_snapshot_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    tmdb_synced_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
