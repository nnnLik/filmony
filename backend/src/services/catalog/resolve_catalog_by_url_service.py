from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from providers.youtube.youtube_url import is_youtube_host
from services.catalog.resolve_catalog_item_service import ResolveCatalogItemService
from services.catalog.resolve_youtube_video_by_url_service import ResolveYoutubeVideoByUrlService
from services.catalog.youtube_video_dto import YoutubeVideoDTO
from services.kinopoisk.client import KinopoiskClientError
from services.kinopoisk.resolve_kinopoisk_film import KinopoiskUrlParseError

_KINOPOISK_HOSTS = frozenset({'kinopoisk.ru', 'www.kinopoisk.ru'})

CatalogByUrlResult = tuple[CatalogItem, Film] | YoutubeVideoDTO


@dataclass
class ResolveCatalogByUrlService:
    """Resolves a catalog item from a provider URL without an explicit provider argument.

    v1 accepts kinopoisk.ru hosts and YouTube watch/shorts/embed URLs.
    """

    _resolve_catalog_item: ResolveCatalogItemService
    _resolve_youtube_video: ResolveYoutubeVideoByUrlService

    class UnsupportedUrlHostError(Exception):
        pass

    class CatalogFilmNotFoundError(Exception):
        pass

    class UpstreamError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _resolve_catalog_item=ResolveCatalogItemService.build(session),
            _resolve_youtube_video=ResolveYoutubeVideoByUrlService.build(),
        )

    def _provider_for_url(self, url: str) -> CatalogProvider:
        stripped = url.strip()
        parsed = urlparse(stripped)
        host = parsed.netloc.lower()
        if host in _KINOPOISK_HOSTS:
            return CatalogProvider.kinopoisk
        if is_youtube_host(stripped):
            return CatalogProvider.youtube
        raise self.UnsupportedUrlHostError

    async def execute(self, *, url: str) -> CatalogByUrlResult:
        provider = self._provider_for_url(url)
        if provider is CatalogProvider.youtube:
            try:
                return await self._resolve_youtube_video.execute(url=url)
            except ResolveYoutubeVideoByUrlService.UnsupportedUrlError:
                raise
            except ResolveYoutubeVideoByUrlService.VideoNotFoundError as exc:
                raise self.CatalogFilmNotFoundError from exc
            except ResolveYoutubeVideoByUrlService.UpstreamError as exc:
                raise self.UpstreamError(str(exc)) from exc

        try:
            return await self._resolve_catalog_item.execute(provider=provider, url=url)
        except KinopoiskUrlParseError:
            raise
        except KinopoiskClientError as exc:
            if '404' in str(exc):
                raise self.CatalogFilmNotFoundError from exc
            raise


__all__ = ('CatalogByUrlResult', 'ResolveCatalogByUrlService')
