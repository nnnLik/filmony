from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReactionCountEntry:
    reaction_type_id: int
    count: int
    image_url: str
    asset_key: str


@dataclass(frozen=True, slots=True)
class ReactionTargetSummary:
    counts: tuple[ReactionCountEntry, ...]
    my_reaction_type_ids: tuple[int, ...]
