from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Self

import httpx

from providers.shared_async_http import httpx_get_idempotent
from utils.http_url import normalize_absolute_http_url


class YoutubeOembedDtoParseError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class YoutubeOembedDTO:
    title: str
    thumbnail_url: str
    author_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        try:
            title = data['title']
            thumbnail_url = data['thumbnail_url']
            author_name = data['author_name']
        except KeyError as exc:
            raise YoutubeOembedDtoParseError(f'missing field {exc}') from exc
        if (
            not isinstance(title, str)
            or not isinstance(thumbnail_url, str)
            or not isinstance(author_name, str)
        ):
            raise YoutubeOembedDtoParseError('invalid field types')
        normalized_thumbnail = normalize_absolute_http_url(thumbnail_url) or thumbnail_url
        return cls(
            title=title,
            thumbnail_url=normalized_thumbnail,
            author_name=author_name,
        )


@dataclass
class YoutubeOembedClient:
    """Fetches public YouTube oEmbed metadata without an API key."""

    class VideoNotFoundError(Exception):
        pass

    class UpstreamError(Exception):
        pass

    _OEMBED_URL: str = 'https://www.youtube.com/oembed'

    async def fetch(self, video_url: str) -> YoutubeOembedDTO:
        try:
            response = await httpx_get_idempotent(
                self._OEMBED_URL,
                params={'url': video_url, 'format': 'json'},
            )
        except httpx.HTTPError as exc:
            raise self.UpstreamError(str(exc)) from exc

        if response.status_code == HTTPStatus.NOT_FOUND:
            raise self.VideoNotFoundError
        if response.status_code != HTTPStatus.OK:
            raise self.UpstreamError(f'unexpected status {response.status_code}')

        try:
            payload = response.json()
        except ValueError as exc:
            raise self.UpstreamError('invalid json response') from exc
        if not isinstance(payload, dict):
            raise self.UpstreamError('json root must be an object')

        try:
            return YoutubeOembedDTO.from_dict(payload)
        except YoutubeOembedDtoParseError as exc:
            raise self.UpstreamError(str(exc)) from exc
