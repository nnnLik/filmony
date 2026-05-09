from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from services.reactions.types import ReactionTargetSummary


class ReactionCountItemResponse(BaseModel):
    reaction_type_id: int
    count: int
    image_url: str
    asset_key: str


class ReactionSummaryResponse(BaseModel):
    counts: list[ReactionCountItemResponse] = Field(default_factory=list)
    my_reaction_type_ids: list[int] = Field(default_factory=list)


class ReactionCatalogItemResponse(BaseModel):
    id: int
    image_url: str
    category_slug: str
    asset_key: str

    model_config = ConfigDict(from_attributes=True)


class ReactionCatalogTabResponse(BaseModel):
    category_slug: str
    label: str
    items: list[ReactionCatalogItemResponse] = Field(default_factory=list)


class ReactionCatalogGroupedResponse(BaseModel):
    recent: list[ReactionCatalogItemResponse] = Field(default_factory=list)
    tabs: list[ReactionCatalogTabResponse] = Field(default_factory=list)


class ReactionActorResponse(BaseModel):
    id: UUID
    profile_slug: str
    display_name: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None


class ReactionActorsListResponse(BaseModel):
    items: list[ReactionActorResponse] = Field(default_factory=list)


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
                asset_key=e.asset_key,
            )
            for e in summary.counts
        ],
        my_reaction_type_ids=list(summary.my_reaction_type_ids),
    )
