from __future__ import annotations

import asyncio
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.reactions.schemas import (
    ReactionActorResponse,
    ReactionActorsListResponse,
    ReactionCatalogGroupedResponse,
    ReactionCatalogItemResponse,
    ReactionCatalogTabResponse,
    UserReactionSetRequest,
    UserReactionSetResponse,
    reaction_target_summary_to_response,
)
from celery_app import app as celery_application
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.reaction_target_kind import ReactionTargetKind
from services.reactions.list_reaction_actors import ListReactionActorsService
from services.reactions.list_reaction_catalog import (
    ListReactionCatalogGroupedService,
    ReactionCatalogItem,
)
from services.reactions.set_or_toggle_user_reaction import (
    ReactionTargetNotFoundError,
    ReactionTypeInvalidError,
    SelfReactionForbiddenError,
    SetOrToggleUserReactionService,
    SetUserReactionInput,
)
from utils.reaction_asset_key import is_safe_reaction_asset_key
from utils.rustfs_get_object import (
    RustfsClientError,
    RustfsKeyNotFoundError,
    get_rustfs_object_bytes,
)

router = APIRouter(prefix='/reactions', tags=['reactions'])


@router.get(
    '/asset/{asset_key:path}',
    summary='Прокси-картинка реакции из RustFS (для клиентов без прямого доступа к RustFS)',
)
async def get_reaction_asset(asset_key: str) -> Response:
    if not is_safe_reaction_asset_key(asset_key):
        raise HTTPException(status_code=404, detail='not found') from None
    internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
    if not internal:
        raise HTTPException(status_code=503, detail='reaction asset proxy not configured') from None
    bucket = settings.reaction_media.rustfs_bucket.strip()
    safe_key = asset_key.lstrip('/')
    access = settings.reaction_media.rustfs_access_key.strip()
    secret = settings.reaction_media.rustfs_secret_key.strip()
    headers: dict[str, str] = {'Cache-Control': 'public, max-age=86400'}

    if access and secret:
        try:
            result = await asyncio.to_thread(
                get_rustfs_object_bytes,
                endpoint_url=internal,
                access_key_id=access,
                secret_access_key=secret,
                bucket=bucket,
                key=safe_key,
            )
        except RustfsKeyNotFoundError:
            raise HTTPException(status_code=404, detail='not found') from None
        except RustfsClientError:
            raise HTTPException(status_code=502, detail='storage unreachable') from None
        media = (
            result.content_type.strip()
            if isinstance(result.content_type, str) and result.content_type.strip()
            else 'application/octet-stream'
        )
        return Response(content=result.body, media_type=media, headers=headers)

    url = f'{internal}/{bucket}/{safe_key}'
    timeout = httpx.Timeout(18.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail='storage unreachable') from exc
    if upstream.status_code != 200:
        raise HTTPException(status_code=404, detail='not found') from None
    ct = upstream.headers.get('content-type')
    media = ct.strip() if isinstance(ct, str) and ct.strip() else 'application/octet-stream'
    return Response(content=upstream.content, media_type=media, headers=headers)


def _parse_target_kind(raw: str) -> ReactionTargetKind:
    try:
        return ReactionTargetKind(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail='invalid target_kind') from None


def _catalog_item_response(row: ReactionCatalogItem) -> ReactionCatalogItemResponse:
    return ReactionCatalogItemResponse(
        id=row.id,
        label=row.label,
        image_url=row.image_url,
        category_slug=row.category_slug,
        asset_key=row.asset_key,
    )


@router.get('/catalog', response_model=ReactionCatalogGroupedResponse, summary='Каталог реакций')
async def list_reaction_catalog(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReactionCatalogGroupedResponse:
    grouped = await ListReactionCatalogGroupedService(db).execute(viewer_user_id=user.id)
    return ReactionCatalogGroupedResponse(
        recent=[_catalog_item_response(r) for r in grouped.recent],
        tabs=[
            ReactionCatalogTabResponse(
                category_slug=tab.category_slug,
                label=tab.label,
                items=[_catalog_item_response(i) for i in tab.items],
            )
            for tab in grouped.tabs
        ],
    )


@router.get('/actors', response_model=ReactionActorsListResponse, summary='Кто поставил реакцию')
async def list_reaction_actors(
    _user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    target_kind: str = Query(..., min_length=1, max_length=32),
    target_id: int = Query(..., ge=1),
    reaction_type_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=50),
) -> ReactionActorsListResponse:
    kind = _parse_target_kind(target_kind)
    rows = await ListReactionActorsService(db).execute(
        target_kind=kind,
        target_id=target_id,
        reaction_type_id=reaction_type_id,
        limit=limit,
    )
    return ReactionActorsListResponse(
        items=[
            ReactionActorResponse(
                id=r.id,
                profile_slug=r.profile_slug,
                display_name=r.display_name,
                username=r.username,
                first_name=r.first_name,
                last_name=r.last_name,
                photo_url=r.photo_url,
            )
            for r in rows
        ]
    )


@router.post('', response_model=UserReactionSetResponse, summary='Поставить или снять реакцию')
async def set_user_reaction(
    body: UserReactionSetRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserReactionSetResponse:
    kind = _parse_target_kind(body.target_kind)
    try:
        outcome = await SetOrToggleUserReactionService(db).execute(
            user.id,
            SetUserReactionInput(
                target_kind=kind,
                target_id=body.target_id,
                reaction_type_id=body.reaction_type_id,
            ),
        )
    except ReactionTypeInvalidError:
        raise HTTPException(status_code=422, detail='invalid reaction_type_id') from None
    except ReactionTargetNotFoundError:
        raise HTTPException(status_code=404, detail='target not found') from None
    except SelfReactionForbiddenError:
        raise HTTPException(status_code=403, detail='self reaction not allowed') from None

    if outcome.reaction_was_added:
        celery_application.send_task(
            'tasks.telegram_engagement.notify_reaction_added',
            kwargs={
                'actor_user_id': str(user.id),
                'target_kind': kind.value,
                'target_id': body.target_id,
                'reaction_type_id': body.reaction_type_id,
            },
        )

    return UserReactionSetResponse(
        target_kind=kind.value,
        target_id=body.target_id,
        reactions=reaction_target_summary_to_response(outcome.summary),
    )
