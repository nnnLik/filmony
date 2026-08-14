from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any, Self
from urllib.parse import urlparse

import httpx

from conf import settings
from providers.playback.dto import PlaybackDescriptor
from providers.shared_async_http import httpx_get_idempotent
from utils.http_url import normalize_absolute_http_url

_PROVIDER = 'pleer.video'


class PleerVideoDtoParseError(Exception):
    pass


def _is_embed_unavailable_error(exc: PleerVideoDtoParseError) -> bool:
    message = str(exc)
    if message in {'missing embeds', 'invalid iframe', 'invalid embed item'}:
        return True
    return message.startswith('missing field') and 'iframe' in message


@dataclass(frozen=True, slots=True)
class PleerVideoFilmDTO:
    kinopoisk_id: int
    title: str
    iframe_url: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        try:
            kinopoisk_id = data['kp_id']
            title = data['title_ru']
            embeds = data['embeds']
        except KeyError as exc:
            raise PleerVideoDtoParseError(f'missing field {exc}') from exc
        if not isinstance(kinopoisk_id, int) or kinopoisk_id < 1:
            raise PleerVideoDtoParseError('invalid kp_id')
        if not isinstance(title, str) or title.strip() == '':
            raise PleerVideoDtoParseError('invalid title_ru')
        if not isinstance(embeds, list) or len(embeds) == 0:
            raise PleerVideoDtoParseError('missing embeds')
        first = embeds[0]
        if not isinstance(first, dict):
            raise PleerVideoDtoParseError('invalid embed item')
        try:
            iframe_raw = first['iframe']
        except KeyError as exc:
            raise PleerVideoDtoParseError(f'missing field {exc}') from exc
        if not isinstance(iframe_raw, str) or iframe_raw.strip() == '':
            raise PleerVideoDtoParseError('invalid iframe')
        iframe_url = normalize_absolute_http_url(iframe_raw.strip()) or iframe_raw.strip()
        parsed = urlparse(iframe_url)
        if parsed.scheme not in {'http', 'https'} or parsed.netloc == '':
            raise PleerVideoDtoParseError('iframe must be absolute http(s) url')
        return cls(
            kinopoisk_id=kinopoisk_id,
            title=title.strip(),
            iframe_url=iframe_url,
        )


@dataclass
class PleerVideoClient:
    """Resolves pleer.video iframe URLs by Kinopoisk id (no API token required)."""

    class UpstreamError(Exception):
        pass

    _api_base_url: str
    _cache_ttl_seconds: int

    @classmethod
    def build(cls) -> Self:
        cfg = settings.playback
        base = (cfg.pleer_video_api_base_url or 'https://pleer.video').rstrip('/')
        return cls(
            _api_base_url=base,
            _cache_ttl_seconds=cfg.cache_ttl_seconds,
        )

    async def resolve(self, kinopoisk_id: int) -> PlaybackDescriptor | None:
        if kinopoisk_id < 1:
            return None
        url = f'{self._api_base_url}/{kinopoisk_id}.json'
        try:
            response = await httpx_get_idempotent(url)
        except httpx.HTTPError as exc:
            raise self.UpstreamError(str(exc)) from exc

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None
        if response.status_code != HTTPStatus.OK:
            raise self.UpstreamError(f'unexpected status {response.status_code}')

        try:
            payload = response.json()
        except ValueError as exc:
            raise self.UpstreamError('invalid json response') from exc
        if not isinstance(payload, dict):
            raise self.UpstreamError('json root must be an object')

        try:
            film = PleerVideoFilmDTO.from_dict(payload)
        except PleerVideoDtoParseError as exc:
            if _is_embed_unavailable_error(exc):
                return None
            raise self.UpstreamError(str(exc)) from exc

        expires_at = datetime.now(tz=UTC) + timedelta(seconds=self._cache_ttl_seconds)
        return PlaybackDescriptor(
            provider=_PROVIDER,
            title=film.title,
            iframe_url=film.iframe_url,
            kinopoisk_id=film.kinopoisk_id,
            expires_at=expires_at,
        )
