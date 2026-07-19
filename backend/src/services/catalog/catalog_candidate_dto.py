"""Unified catalog candidate rows for mixed Kinopoisk + RAWG search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models.catalog_item import CatalogProvider

CatalogCandidateKind = Literal['film', 'game']
CatalogCandidateSource = Literal['local', 'remote']


@dataclass(frozen=True, slots=True)
class CatalogCandidateDTO:
    """One mixed-source catalog hit for create-flow candidate lists."""

    provider: CatalogProvider
    external_id: str
    kind: CatalogCandidateKind
    kind_hint: CatalogCandidateKind | None
    title: str
    subtitle: str | None
    cover_url: str | None
    catalog_item_id: int | None
    source: CatalogCandidateSource
    degraded: bool | None = None

    @property
    def candidate_id(self) -> str:
        return f'{self.provider.value}:{self.external_id}'


@dataclass(frozen=True, slots=True)
class SearchCatalogCandidatesResult:
    """Merged candidate list plus pagination and degraded-source metadata."""

    items: tuple[CatalogCandidateDTO, ...]
    has_more: bool
    degraded_sources: tuple[str, ...]


__all__ = (
    'CatalogCandidateDTO',
    'CatalogCandidateKind',
    'CatalogCandidateSource',
    'SearchCatalogCandidatesResult',
)
