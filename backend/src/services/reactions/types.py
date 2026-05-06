from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReactionCountEntry:
    reaction_type_id: int
    count: int
    image_url: str
    label: str | None
    sort_order: int


@dataclass(frozen=True, slots=True)
class ReactionTargetSummary:
    counts: tuple[ReactionCountEntry, ...]
    my_reaction_type_id: int | None
