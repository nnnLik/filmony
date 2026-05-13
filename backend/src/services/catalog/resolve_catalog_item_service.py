from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.film import Film
from services.kinopoisk.resolve_kinopoisk_film import ResolveKinopoiskFilmService


@dataclass
class ResolveCatalogItemService:
    """Resolves an external catalog reference (URL + provider) to a persisted CatalogItem.

    Links the canonical Film row for supported providers so legacy film-based flows keep working
    alongside catalog-first identifiers.
    """

    _session: AsyncSession
    _resolve_kinopoisk_film: ResolveKinopoiskFilmService

    class UnsupportedCatalogProviderError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _resolve_kinopoisk_film=ResolveKinopoiskFilmService(session),
        )

    async def execute(self, *, provider: str, url: str) -> tuple[CatalogItem, Film]:
        key = provider.strip().lower()
        if key == 'kinopoisk':
            film = await self._resolve_kinopoisk_film.execute(url)
            item = await self._ensure_kinopoisk_catalog_item(film)
            return item, film
        raise self.UnsupportedCatalogProviderError

    async def _ensure_kinopoisk_catalog_item(self, film: Film) -> CatalogItem:
        external_id = str(film.kinopoisk_id)
        existing = (
            await self._session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == 'kinopoisk',
                    CatalogItem.external_id == external_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.film_id != film.id:
                existing.film_id = film.id
                await self._session.commit()
                await self._session.refresh(existing)
            return existing

        item = CatalogItem(
            provider='kinopoisk',
            external_id=external_id,
            film_id=film.id,
        )
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item


__all__ = ('ResolveCatalogItemService',)
