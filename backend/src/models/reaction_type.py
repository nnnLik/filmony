from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ReactionType(Base):
    category_slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    asset_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
