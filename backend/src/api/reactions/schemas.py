from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from services.reactions.types import ReactionTargetSummary


class ReactionCountItemResponse(BaseModel):
    reaction_type_id: int
    count: int
    image_url: str
    label: str | None = None


class ReactionSummaryResponse(BaseModel):
    counts: list[ReactionCountItemResponse] = Field(default_factory=list)
    my_reaction_type_id: int | None = None


class ReactionCatalogItemResponse(BaseModel):
    id: int
    label: str | None
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class ReactionCatalogListResponse(BaseModel):
    items: list[ReactionCatalogItemResponse] = Field(default_factory=list)


class UserReactionSetRequest(BaseModel):
    target_kind: str = Field(..., min_length=1, max_length=32)
    target_id: int = Field(..., ge=1)
    reaction_type_id: int = Field(..., ge=1)

    model_config = ConfigDict(extra='forbid')


class UserReactionSetResponse(BaseModel):
    target_kind: str
    target_id: int
    reactions: ReactionSummaryResponse


def reaction_target_summary_to_response(summary: ReactionTargetSummary) -> ReactionSummaryResponse:
    return ReactionSummaryResponse(
        counts=[
            ReactionCountItemResponse(
                reaction_type_id=e.reaction_type_id,
                count=e.count,
                image_url=e.image_url,
                label=e.label,
            )
            for e in summary.counts
        ],
        my_reaction_type_id=summary.my_reaction_type_id,
    )
