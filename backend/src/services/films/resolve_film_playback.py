from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from providers.playback import PleerVideoClient
from providers.playback.dto import PlaybackDescriptor
from services.films.get_film_by_id import GetFilmByIdService


@dataclass(frozen=True, slots=True)
class FilmPlaybackDTO:
    provider: str
    title: str
    iframe_url: str
    film_id: int
    kinopoisk_id: int
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    descriptor: PlaybackDescriptor
    expires_at: datetime


_playback_cache: dict[int, _CacheEntry] = {}


@dataclass
class ResolveFilmPlaybackService:
    """Resolves an embeddable watch URL for a catalog film via pleer.video."""

    _film_dao: GetFilmByIdService
    _pleer_client: PleerVideoClient

    class FilmNotFound(Exception):
        pass

    class PlaybackUnavailable(Exception):
        pass

    class PlaybackProviderError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _film_dao=GetFilmByIdService(session),
            _pleer_client=PleerVideoClient.build(),
        )

    async def execute(self, film_id: int, _viewer_user_id) -> FilmPlaybackDTO:
        if not settings.playback.enabled:
            raise self.PlaybackUnavailable

        film = await self._film_dao.execute(film_id)
        if film is None:
            raise self.FilmNotFound

        kinopoisk_id = film.kinopoisk_id
        if kinopoisk_id is None or kinopoisk_id < 1:
            raise self.PlaybackUnavailable

        descriptor = self._cached_descriptor(kinopoisk_id)
        if descriptor is None:
            try:
                descriptor = await self._pleer_client.resolve(kinopoisk_id)
            except PleerVideoClient.UpstreamError as exc:
                raise self.PlaybackProviderError from exc
            if descriptor is None or not descriptor.iframe_url.strip():
                raise self.PlaybackUnavailable
            self._store_descriptor(kinopoisk_id, descriptor)

        if not descriptor.iframe_url.strip():
            raise self.PlaybackUnavailable

        return FilmPlaybackDTO(
            provider=descriptor.provider,
            title=descriptor.title,
            iframe_url=descriptor.iframe_url,
            film_id=film.id,
            kinopoisk_id=kinopoisk_id,
            expires_at=descriptor.expires_at,
        )

    def _cached_descriptor(self, kinopoisk_id: int) -> PlaybackDescriptor | None:
        entry = _playback_cache.get(kinopoisk_id)
        if entry is None:
            return None
        if entry.expires_at <= datetime.now(tz=UTC):
            _playback_cache.pop(kinopoisk_id, None)
            return None
        return entry.descriptor

    def _store_descriptor(self, kinopoisk_id: int, descriptor: PlaybackDescriptor) -> None:
        _playback_cache[kinopoisk_id] = _CacheEntry(
            descriptor=descriptor,
            expires_at=descriptor.expires_at,
        )
