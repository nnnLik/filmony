from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReactionActorEntry:
    id: UUID
    profile_slug: str
    display_name: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None


@dataclass(frozen=True, slots=True)
class ReactionCountEntry:
    reaction_type_id: int
    count: int
    image_url: str
    asset_key: str
    reactors: tuple[ReactionActorEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class ReactionTargetSummary:
    counts: tuple[ReactionCountEntry, ...]
    my_reaction_type_ids: tuple[int, ...]
