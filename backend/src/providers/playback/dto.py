from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PlaybackDescriptor:
    provider: str
    title: str
    iframe_url: str
    kinopoisk_id: int
    expires_at: datetime
