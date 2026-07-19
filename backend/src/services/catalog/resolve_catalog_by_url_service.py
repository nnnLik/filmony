from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from services.catalog.resolve_catalog_item_service import ResolveCatalogItemService
from services.kinopoisk.client import KinopoiskClientError
from services.kinopoisk.resolve_kinopoisk_film import KinopoiskUrlParseError

_KINOPOISK_HOSTS = frozenset({'kinopoisk.ru', 'www.kinopoisk.ru'})


@dataclass
class ResolveCatalogByUrlService:
    """Resolves a catalog item from a provider URL without an explicit provider argument.

    v1 accepts only kinopoisk.ru / www.kinopoisk.ru hosts and delegates to ResolveCatalogItemService
    with provider=kinopoisk so catalog rows stay aligned with the legacy resolve flow.
    """

    _resolve_catalog_item: ResolveCatalogItemService

    class UnsupportedUrlHostError(Exception):
        pass

    class CatalogFilmNotFoundError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_resolve_catalog_item=ResolveCatalogItemService.build(session))

    def _provider_for_url(self, url: str) -> CatalogProvider:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower()
        if host in _KINOPOISK_HOSTS:
            return CatalogProvider.kinopoisk
        raise self.UnsupportedUrlHostError

    async def execute(self, *, url: str) -> tuple[CatalogItem, Film]:
        provider = self._provider_for_url(url)
        try:
            return await self._resolve_catalog_item.execute(provider=provider, url=url)
        except KinopoiskUrlParseError:
            raise
        except KinopoiskClientError as exc:
            if '404' in str(exc):
                raise self.CatalogFilmNotFoundError from exc
            raise


__all__ = ('ResolveCatalogByUrlService',)
