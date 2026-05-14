"""Normalized catalog search hits for persisted RAWG games."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models.catalog_item import CatalogProvider


@dataclass(frozen=True, slots=True)
class RawgCatalogSearchHitDTO:
    """One search row after local index + optional RAWG fallback."""

    provider: CatalogProvider
    external_id: str
    kind: Literal['game']
    title: str
    subtitle: str | None
    cover: str | None
    source: Literal['local', 'remote']
    catalog_item_id: int


__all__ = ('RawgCatalogSearchHitDTO',)
