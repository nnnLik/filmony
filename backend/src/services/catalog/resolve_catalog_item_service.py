from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from services.catalog.ttl_coalescing_cache import CATALOG_RESOLVE_IDS_CACHE
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

    async def _catalog_pair_ids(self, *, url: str) -> tuple[int, int]:
        film = await self._resolve_kinopoisk_film.execute(url)
        item = await self._ensure_kinopoisk_catalog_item(film)
        return item.id, film.id

    async def execute(self, *, provider: CatalogProvider, url: str) -> tuple[CatalogItem, Film]:
        if provider is CatalogProvider.no_provider:
            raise self.UnsupportedCatalogProviderError
        if provider is not CatalogProvider.kinopoisk:
            raise self.UnsupportedCatalogProviderError

        key = f'catalog:resolve:{provider.value}:{url.strip()}'
        c_id, f_id = await CATALOG_RESOLVE_IDS_CACHE.get_or_fetch(
            key,
            lambda: self._catalog_pair_ids(url=url),
        )
        item = await self._session.get(CatalogItem, c_id)
        film = await self._session.get(Film, f_id)
        if item is None or film is None:
            return await self._execute_uncached(url)
        return item, film

    async def _execute_uncached(self, url: str) -> tuple[CatalogItem, Film]:
        film = await self._resolve_kinopoisk_film.execute(url)
        item = await self._ensure_kinopoisk_catalog_item(film)
        return item, film

    async def _ensure_kinopoisk_catalog_item(self, film: Film) -> CatalogItem:
        external_id = str(film.kinopoisk_id)
        existing = (
            await self._session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.kinopoisk,
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
            provider=CatalogProvider.kinopoisk,
            external_id=external_id,
            film_id=film.id,
        )
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item


__all__ = ('ResolveCatalogItemService',)
