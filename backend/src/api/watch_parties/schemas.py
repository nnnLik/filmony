from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WatchPartyCreateRequest(BaseModel):
    film_id: int = Field(..., ge=1)


class WatchPartyCreateResponse(BaseModel):
    id: UUID
    invite_slug: str
    invite_url: str


class WatchPartyMemberResponse(BaseModel):
    user_id: UUID
    display_name: str
    photo_url: str | None
    role: str
    status: str
    joined_at: str


class WatchPartySnapshotResponse(BaseModel):
    id: UUID
    invite_slug: str
    invite_url: str
    status: str
    film_id: int
    film_title: str
    film_poster_url: str | None
    playback_iframe_url: str
    playback_expires_at: str
    playback_state: dict
    host_user_id: UUID
    members: list[WatchPartyMemberResponse]
    viewer_role: str | None
    viewer_status: str | None


class WatchPartySlugResolveResponse(BaseModel):
    party_id: UUID
    invite_slug: str
    status: str


class ActivePartyConflictResponse(BaseModel):
    active_party_id: UUID
    invite_slug: str


class WatchPartyKickRequest(BaseModel):
    user_id: UUID


class WatchPartyPlaybackRequest(BaseModel):
    action: Literal['play', 'pause', 'seek']
    position_ms: int | None = Field(default=None, ge=0)


class WatchPartyMessageCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=500)


class WatchPartyMessageResponse(BaseModel):
    id: int
    author_user_id: UUID
    body: str
    created_at: str


class WatchPartyTypingRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=120)


class WatchPartyInviteRequest(BaseModel):
    user_ids: list[UUID] = Field(..., min_length=1, max_length=32)


class WatchPartyWatchingBatchRequest(BaseModel):
    user_ids: list[UUID] = Field(default_factory=list, max_length=100)


class WatchPartyWatchingItemResponse(BaseModel):
    film_id: int
    film_title: str
    party_id: UUID | None = None


class WatchPartyWatchingBatchResponse(BaseModel):
    items: dict[str, WatchPartyWatchingItemResponse]


class WatchPartyBridgeResponse(BaseModel):
    watch_session_id: UUID
