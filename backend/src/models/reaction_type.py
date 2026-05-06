from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ReactionType(Base):
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category_slug: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    asset_key: Mapped[str | None] = mapped_column(String(512), nullable=True, unique=True)
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
