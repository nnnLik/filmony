from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from providers.youtube.youtube_oembed_client import YoutubeOembedClient
from providers.youtube.youtube_url import canonical_youtube_url, parse_video_id
from services.catalog.youtube_video_dto import YoutubeVideoDTO


@dataclass
class ResolveYoutubeVideoByUrlService:
    """Resolves a YouTube video from a watch/shorts/embed URL via public oEmbed metadata."""

    _oembed_client: YoutubeOembedClient

    class UnsupportedUrlError(Exception):
        pass

    class VideoNotFoundError(Exception):
        pass

    class UpstreamError(Exception):
        pass

    @classmethod
    def build(cls) -> Self:
        return cls(_oembed_client=YoutubeOembedClient())

    async def execute(self, *, url: str) -> YoutubeVideoDTO:
        video_id = parse_video_id(url)
        if video_id is None:
            raise self.UnsupportedUrlError

        canonical_url = canonical_youtube_url(video_id)
        try:
            oembed = await self._oembed_client.fetch(canonical_url)
        except YoutubeOembedClient.VideoNotFoundError as exc:
            raise self.VideoNotFoundError from exc
        except YoutubeOembedClient.UpstreamError as exc:
            raise self.UpstreamError(str(exc)) from exc

        return YoutubeVideoDTO(
            video_id=video_id,
            canonical_url=canonical_url,
            title=oembed.title,
            cover_url=oembed.thumbnail_url,
            summary=oembed.author_name,
        )


__all__ = ('ResolveYoutubeVideoByUrlService',)
