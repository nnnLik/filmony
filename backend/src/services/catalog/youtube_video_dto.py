from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class YoutubeVideoDTO:
    video_id: str
    canonical_url: str
    title: str
    cover_url: str
    summary: str
