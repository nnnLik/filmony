from __future__ import annotations

import asyncio
import json
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.feed_posts.schemas import (
    FeedPostCreateRequest,
    FeedPostImageUploadResponse,
    FeedPostResponse,
)
from celery_app import app as celery_application
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from services.feed_posts import (
    FEED_POST_IMAGE_MAX_BYTES,
    CreateFeedPostInput,
    CreateFeedPostService,
    FeedPostImageUploadError,
    FeedPostNotFoundError,
    FeedPostValidationError,
    GetFeedPostByIdService,
    ReferencedMovieCardNotFoundError,
    SourceCommentForbiddenError,
    SourceCommentNotFoundError,
    UploadFeedPostImageService,
)
from utils.feed_post_media_key import is_safe_feed_post_media_key
from utils.rustfs_get_object import (
    RustfsClientError,
    RustfsKeyNotFoundError,
    get_rustfs_object_bytes,
)

router = APIRouter(prefix='/feed-posts', tags=['feed-posts'])


async def _read_upload_body(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail='file too large') from None
        chunks.append(chunk)
    return b''.join(chunks)


@router.post('/upload', response_model=FeedPostImageUploadResponse)
async def upload_feed_post_image(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> FeedPostImageUploadResponse:
    content_type = (file.content_type or '').strip()
    try:
        data = await _read_upload_body(file, FEED_POST_IMAGE_MAX_BYTES)
        url = await UploadFeedPostImageService.build().execute(
            user_id=user.id,
            content_type=content_type,
            data=data,
        )
    except HTTPException:
        raise
    except FeedPostImageUploadError as e:
        msg = str(e).lower()
        if 'not configured' in msg:
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return FeedPostImageUploadResponse(url=url)


@router.get(
    '/media/{media_key:path}',
    summary='Картинка поста из RustFS (без Bearer в img src)',
)
async def get_feed_post_media(media_key: str) -> Response:
    if not is_safe_feed_post_media_key(media_key):
        raise HTTPException(status_code=404, detail='not found') from None
    internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
    if not internal:
        raise HTTPException(status_code=503, detail='media proxy not configured') from None
    bucket = settings.reaction_media.rustfs_bucket.strip()
    safe_key = media_key.lstrip('/')
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


@router.post('', response_model=FeedPostResponse)
async def create_feed_post(
    payload: FeedPostCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
) -> FeedPostResponse:
    try:
        created = await CreateFeedPostService.build(db).execute(
            user.id,
            CreateFeedPostInput(
                body=payload.body,
                image_url=payload.image_url,
                referenced_movie_card_id=payload.referenced_movie_card_id,
                source_comment_id=payload.source_comment_id,
            ),
        )
    except FeedPostValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ReferencedMovieCardNotFoundError:
        raise HTTPException(status_code=400, detail='referenced movie card not found') from None
    except SourceCommentNotFoundError:
        raise HTTPException(status_code=404, detail='source comment not found') from None
    except SourceCommentForbiddenError:
        raise HTTPException(
            status_code=403, detail='source comment belongs to another user'
        ) from None

    post = created.post
    if created.mentioned_user_ids:
        celery_application.tasks['tasks.telegram_engagement.notify_feed_post_mentions'].delay(
            actor_user_id=str(user.id),
            feed_post_id=post.id,
            recipient_user_ids_json=json.dumps([str(x) for x in created.mentioned_user_ids]),
        )

    return FeedPostResponse.model_validate(post)


@router.get('/{post_id}', response_model=FeedPostResponse)
async def get_feed_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
) -> FeedPostResponse:
    try:
        post = await GetFeedPostByIdService.build(db).execute(post_id)
    except FeedPostNotFoundError:
        raise HTTPException(status_code=404, detail='feed post not found') from None
    return FeedPostResponse.model_validate(post)
