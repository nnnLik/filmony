from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.collections.schemas import (
    CollectionFilmItemResponse,
    CollectionFilmsPageResponse,
    CollectionListResponse,
    CollectionSummaryResponse,
    ProfilePinnedCollectionsResponse,
    UserCollectionProgressResponse,
)
from api.films.schemas import FilmAwardBadgeResponse
from core.database import get_db
from deps.auth import CurrentUser, OptionalUser
from models.collection import CollectionKind
from services.collections.get_collection import GetCollectionService
from services.collections.list_collection_films import ListCollectionFilmsService
from services.collections.list_collections import CollectionSummaryDTO, ListCollectionsService
from services.collections.list_profile_pinned_collections import ListProfilePinnedCollectionsService
from services.collections.pin_collection import PinCollectionService
from services.collections.unpin_collection import UnpinCollectionService
from services.profile.get_public_user_by_id import GetPublicUserByIdService

router = APIRouter(prefix='/collections', tags=['collections'])
me_pins_router = APIRouter(prefix='/me/collection-pins', tags=['collections'])
profiles_router = APIRouter(prefix='/profiles', tags=['profiles'])


def _progress_response(dto: CollectionSummaryDTO) -> UserCollectionProgressResponse | None:
    if dto.viewer_progress is None:
        return None
    return UserCollectionProgressResponse(
        rated_count=dto.viewer_progress.rated_count,
        total_count=dto.viewer_progress.total_count,
        completed_at=dto.viewer_progress.completed_at,
    )


def _summary_response(dto: CollectionSummaryDTO) -> CollectionSummaryResponse:
    return CollectionSummaryResponse(
        slug=dto.slug,
        kind=dto.kind,
        title=dto.title,
        description=dto.description,
        season_year=dto.season_year,
        film_count=dto.film_count,
        content_updated_at=dto.content_updated_at,
        viewer_progress=_progress_response(dto),
        is_pinned=dto.is_pinned,
    )


@router.get('', response_model=CollectionListResponse, summary='Active global collections')
async def list_collections(
    viewer: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    kind: CollectionKind | None = None,
) -> CollectionListResponse:
    viewer_id: UUID | None = viewer.id if viewer is not None else None
    items = await ListCollectionsService.build(db).execute(
        kind=kind,
        viewer_user_id=viewer_id,
    )
    return CollectionListResponse(items=[_summary_response(item) for item in items])


@router.get(
    '/{slug}', response_model=CollectionSummaryResponse, summary='Collection header by slug'
)
async def get_collection(
    slug: str,
    viewer: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionSummaryResponse:
    viewer_id: UUID | None = viewer.id if viewer is not None else None
    try:
        detail = await GetCollectionService.build(db).execute(slug, viewer_user_id=viewer_id)
    except GetCollectionService.CollectionNotFound:
        raise HTTPException(status_code=404, detail='collection not found') from None
    return _summary_response(detail)


@router.get(
    '/{slug}/films',
    response_model=CollectionFilmsPageResponse,
    summary='Paginated films in a collection',
)
async def list_collection_films(
    slug: str,
    viewer: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> CollectionFilmsPageResponse:
    viewer_id: UUID | None = viewer.id if viewer is not None else None
    try:
        page = await ListCollectionFilmsService.build(db).execute(
            slug,
            cursor,
            limit,
            viewer_user_id=viewer_id,
        )
    except ListCollectionFilmsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    except ListCollectionFilmsService.CollectionNotFound:
        raise HTTPException(status_code=404, detail='collection not found') from None
    return CollectionFilmsPageResponse(
        items=[
            CollectionFilmItemResponse(
                film_id=item.film_id,
                title=item.title,
                year=item.year,
                poster_url=item.poster_url,
                viewer_has_rated=item.viewer_has_rated,
                viewer_card_id=item.viewer_card_id,
                award_badges=[
                    FilmAwardBadgeResponse(
                        kind=badge.kind.value,
                        ceremony_year=badge.ceremony_year,
                    )
                    for badge in item.award_badges
                ],
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
        total_count=page.total_count,
    )


@me_pins_router.post(
    '/{slug}',
    status_code=204,
    response_class=Response,
    summary='Pin a collection on profile',
)
async def pin_collection(
    slug: str,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await PinCollectionService.build(db).execute(viewer.id, slug)
    except PinCollectionService.CollectionNotFound:
        raise HTTPException(status_code=404, detail='collection not found') from None
    except PinCollectionService.PinLimitExceeded:
        raise HTTPException(status_code=409, detail='pin limit exceeded') from None
    return Response(status_code=204)


@me_pins_router.delete(
    '/{slug}',
    status_code=204,
    response_class=Response,
    summary='Unpin a collection from profile',
)
async def unpin_collection(
    slug: str,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await UnpinCollectionService.build(db).execute(viewer.id, slug)
    except UnpinCollectionService.CollectionNotFound:
        raise HTTPException(status_code=404, detail='collection not found') from None
    return Response(status_code=204)


@profiles_router.get(
    '/{user_id}/collections',
    response_model=ProfilePinnedCollectionsResponse,
    summary='Profile owner pinned collections',
)
async def list_profile_pinned_collections(
    user_id: UUID,
    _viewer: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfilePinnedCollectionsResponse:
    user = await GetPublicUserByIdService(db).execute(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='user not found') from None
    items = await ListProfilePinnedCollectionsService.build(db).execute(user_id)
    return ProfilePinnedCollectionsResponse(items=[_summary_response(item) for item in items])
