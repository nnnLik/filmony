from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

import httpx
import orjson
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.feed_post_feed_mapping import (
    feed_post_feed_item_to_response,
    inline_mention_snippets_to_response,
    inline_user_card_snippets_to_response,
)
from api.cards.schemas import FeedPostFeedItemResponse, UserCardCommentAuthorResponse
from api.feed_posts.schemas import (
    FeedPostCommentCreateRequest,
    FeedPostCommentListResponse,
    FeedPostCommentResponse,
    FeedPostCreateRequest,
    FeedPostImageUploadResponse,
    FeedPostResponse,
)
from api.reactions.schemas import reaction_target_summary_to_response
from celery_app import app as celery_application
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.user import User
from services.cards.inline_user_card_ref_tokens import batch_resolve_inline_user_card_refs
from services.feed.global_feed_head_broker import bump_global_feed_head_version
from services.feed_posts import (
    FEED_POST_IMAGE_MAX_BYTES,
    CreateFeedPostInput,
    CreateFeedPostService,
    FeedPostImageUploadError,
    FeedPostNotFoundError,
    FeedPostValidationError,
    ReferencedUserCardNotFoundError,
    SourceCommentForbiddenError,
    SourceCommentNotFoundError,
    UploadFeedPostImageService,
)
from services.feed_posts.create_feed_post_comment import (
    CreateFeedPostCommentInput,
    CreateFeedPostCommentService,
    FeedPostCommentValidationError,
    ParentCommentMismatchError,
    ParentCommentNotFoundError,
)
from services.feed_posts.get_feed_post_feed_item import GetFeedPostFeedItemService
from services.feed_posts.list_feed_post_comments import (
    CommentNotFoundError,
    FeedPostCommentItem,
    ListFeedPostCommentsService,
)
from services.profile.batch_resolve_inline_mentions import batch_resolve_inline_mentions
from services.reactions import GetReactionSummariesForTargetsService
from services.subscriptions.list_follower_user_ids_for_following_user import (
    ListFollowerUserIdsForFollowingUserService,
)
from utils.feed_post_media_key import is_safe_feed_post_media_key
from utils.rustfs_get_object import (
    RustfsClientError,
    RustfsKeyNotFoundError,
    get_rustfs_object_bytes,
)

router = APIRouter(prefix='/feed-posts', tags=['feed-posts'])


def _feed_post_comment_item_to_response(item: FeedPostCommentItem) -> FeedPostCommentResponse:
    a = item.author
    return FeedPostCommentResponse(
        id=item.id,
        feed_post_id=item.feed_post_id,
        parent_comment_id=item.parent_comment_id,
        text=item.text,
        created_at=item.created_at,
        replies_count=item.replies_count,
        total_descendants_count=item.total_descendants_count,
        author=UserCardCommentAuthorResponse(
            id=a.id,
            profile_slug=a.profile_slug,
            username=a.username,
            first_name=a.first_name,
            last_name=a.last_name,
            photo_url=a.photo_url,
            display_name=a.display_name,
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
        referenced_movie_cards=inline_user_card_snippets_to_response(item.referenced_inline_user_cards),
        referenced_mentions=inline_mention_snippets_to_response(item.referenced_mentions),
    )


async def _load_feed_post_comment_response(
    db: AsyncSession, comment_id: int, viewer_user_id: UUID
) -> FeedPostCommentResponse:
    row = (
        await db.execute(
            select(FeedPostComment, User)
            .join(User, User.id == FeedPostComment.user_id)
            .where(FeedPostComment.id == comment_id)
        )
    ).one()
    comment, author = row
    _, _, rx, _ = await GetReactionSummariesForTargetsService(db).execute(
        viewer_user_id=viewer_user_id,
        user_card_ids=[],
        comment_ids=[],
        feed_post_comment_ids=[comment.id],
        feed_post_ids=[],
    )
    (snips,) = await batch_resolve_inline_user_card_refs(db, [(author.id, comment.text or '')])
    (mens,) = await batch_resolve_inline_mentions(db, [comment.text or ''])
    return FeedPostCommentResponse(
        id=comment.id,
        feed_post_id=comment.feed_post_id,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        created_at=comment.created_at,
        replies_count=0,
        total_descendants_count=0,
        author=UserCardCommentAuthorResponse(
            id=author.id,
            profile_slug=author.profile_slug,
            username=author.username,
            first_name=author.first_name,
            last_name=author.last_name,
            photo_url=author.photo_url,
            display_name=author.display_name,
        ),
        reactions=reaction_target_summary_to_response(rx[comment.id]),
        referenced_movie_cards=inline_user_card_snippets_to_response(snips),
        referenced_mentions=inline_mention_snippets_to_response(mens),
    )


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
                referenced_user_card_id=payload.referenced_movie_card_id,
                source_comment_id=payload.source_comment_id,
            ),
        )
    except FeedPostValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ReferencedUserCardNotFoundError:
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
            recipient_user_ids_json=orjson.dumps(
                [str(x) for x in created.mentioned_user_ids]
            ).decode(),
        )

    exclude = frozenset(created.mentioned_user_ids) if created.mentioned_user_ids else None
    follower_ids = await ListFollowerUserIdsForFollowingUserService.build(db).execute(
        user.id,
        exclude_user_ids=exclude,
    )
    if follower_ids:
        celery_application.tasks['tasks.telegram_engagement.notify_followers_new_feed_post'].delay(
            actor_user_id=str(user.id),
            feed_post_id=post.id,
            recipient_user_ids_json=orjson.dumps([str(x) for x in follower_ids]).decode(),
        )

    await bump_global_feed_head_version()
    return FeedPostResponse.model_validate(post)


@router.get(
    '/{post_id}/comments',
    response_model=FeedPostCommentListResponse,
    summary='Комментарии к посту ленты',
)
async def list_feed_post_comments_route(
    post_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> FeedPostCommentListResponse:
    try:
        page = await ListFeedPostCommentsService.build(db).execute(
            viewer.id,
            feed_post_id=post_id,
            parent_comment_id=None,
            cursor=cursor,
            limit=min(limit, 50),
            flat=True,
        )
    except FeedPostNotFoundError:
        raise HTTPException(status_code=404, detail='feed post not found') from None
    return FeedPostCommentListResponse(
        items=[_feed_post_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{post_id}/comments/{comment_id}/replies',
    response_model=FeedPostCommentListResponse,
    summary='Ответы на комментарий к посту',
)
async def list_feed_post_comment_replies_route(
    post_id: int,
    comment_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> FeedPostCommentListResponse:
    try:
        page = await ListFeedPostCommentsService.build(db).execute(
            viewer.id,
            feed_post_id=post_id,
            parent_comment_id=comment_id,
            cursor=cursor,
            limit=min(limit, 50),
        )
    except FeedPostNotFoundError:
        raise HTTPException(status_code=404, detail='feed post not found') from None
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail='comment not found') from None
    return FeedPostCommentListResponse(
        items=[_feed_post_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.post(
    '/{post_id}/comments',
    response_model=FeedPostCommentResponse,
    summary='Создать комментарий к посту',
)
async def create_feed_post_comment_route(
    post_id: int,
    body: FeedPostCommentCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FeedPostCommentResponse:
    try:
        outcome = await CreateFeedPostCommentService.build(db).execute(
            post_id,
            user.id,
            CreateFeedPostCommentInput(
                text=body.text,
                parent_comment_id=body.parent_comment_id,
            ),
        )
    except FeedPostNotFoundError:
        raise HTTPException(status_code=404, detail='feed post not found') from None
    except ParentCommentNotFoundError:
        raise HTTPException(status_code=404, detail='parent comment not found') from None
    except ParentCommentMismatchError:
        raise HTTPException(
            status_code=422, detail='parent comment belongs to another post'
        ) from None
    except FeedPostCommentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    created = outcome.comment
    mention_recipients = list(outcome.mentioned_user_ids)
    if body.parent_comment_id is not None:
        parent_author_id = (
            await db.execute(
                select(FeedPostComment.user_id).where(FeedPostComment.id == body.parent_comment_id)
            )
        ).scalar_one_or_none()
        if parent_author_id is not None:
            mention_recipients = [uid for uid in mention_recipients if uid != parent_author_id]
    else:
        post_owner_id = (
            await db.execute(select(FeedPost.user_id).where(FeedPost.id == post_id))
        ).scalar_one_or_none()
        if post_owner_id is not None:
            mention_recipients = [uid for uid in mention_recipients if uid != post_owner_id]

    if body.parent_comment_id is None:
        celery_application.tasks['tasks.telegram_engagement.notify_feed_post_root_comment'].delay(
            actor_user_id=str(user.id),
            feed_post_id=post_id,
            comment_text=created.text,
        )
    else:
        celery_application.tasks['tasks.telegram_engagement.notify_feed_post_comment_reply'].delay(
            actor_user_id=str(user.id),
            feed_post_id=post_id,
            parent_comment_id=body.parent_comment_id,
            reply_text=created.text,
        )

    if mention_recipients:
        celery_application.tasks[
            'tasks.telegram_engagement.notify_feed_post_comment_mentions'
        ].delay(
            actor_user_id=str(user.id),
            feed_post_id=post_id,
            comment_id=created.id,
            recipient_user_ids_json=orjson.dumps([str(x) for x in mention_recipients]).decode(),
        )

    return await _load_feed_post_comment_response(db, created.id, user.id)


@router.get('/{post_id}', response_model=FeedPostFeedItemResponse)
async def get_feed_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUser,
) -> FeedPostFeedItemResponse:
    try:
        item = await GetFeedPostFeedItemService.build(db).execute(post_id, user.id)
    except FeedPostNotFoundError:
        raise HTTPException(status_code=404, detail='feed post not found') from None
    return feed_post_feed_item_to_response(item)
