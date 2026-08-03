from __future__ import annotations

from sqlalchemy import JSON, Integer, String, Text
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
    franchise_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
