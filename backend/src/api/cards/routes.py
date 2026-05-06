from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.schemas import (
    CardCreateRequest,
    CardDetailResponse,
    CardResponse,
    MovieCardCommentAuthorResponse,
    MovieCardCommentCreateRequest,
    MovieCardCommentListResponse,
    MovieCardCommentResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from models.movie_card_comment import MovieCardComment
from models.movie_card_tag import MovieCardTag
from models.user import User
from services.cards.create_movie_card import (
    CreateMovieCardInput,
    CreateMovieCardService,
    FilmNotFoundError,
    MovieCardAlreadyExistsError,
    MovieCardValidationError,
)
from services.cards.create_movie_card_comment import (
    CreateMovieCardCommentInput,
    CreateMovieCardCommentService,
    MovieCardCommentValidationError,
    ParentCommentMismatchError,
    ParentCommentNotFoundError,
)
from services.cards.create_movie_card_comment import (
    MovieCardNotFoundError as CommentMovieCardNotFoundError,
)
from services.cards.get_movie_card_details import GetMovieCardDetailsService, MovieCardNotFoundError
from services.cards.list_movie_card_comments import (
    CommentNotFoundError,
    ListMovieCardCommentsService,
)
from services.cards.list_movie_card_comments import (
    MovieCardNotFoundError as ListCommentsMovieCardNotFoundError,
)

router = APIRouter(prefix='/cards', tags=['cards'])


async def _load_comment_response(db: AsyncSession, comment_id: int) -> MovieCardCommentResponse:
    row = (
        await db.execute(
            select(MovieCardComment, User)
            .join(User, User.id == MovieCardComment.user_id)
            .where(MovieCardComment.id == comment_id)
        )
    ).one()
    comment, author = row
    return MovieCardCommentResponse(
        id=comment.id,
        movie_card_id=comment.movie_card_id,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        created_at=comment.created_at,
        replies_count=0,
        total_descendants_count=0,
        author=MovieCardCommentAuthorResponse(
            id=author.id,
            profile_slug=author.profile_slug,
            username=author.username,
            first_name=author.first_name,
            last_name=author.last_name,
            photo_url=author.photo_url,
            display_name=author.display_name,
        ),
    )


@router.post('', response_model=CardResponse, summary='Создать карточку фильма')
async def create_card(
    body: CardCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardResponse:
    try:
        card = await CreateMovieCardService(db).execute(
            user.id,
            CreateMovieCardInput(
                film_id=body.film_id,
                kinopoisk_id=body.kinopoisk_id,
                genres=body.genres,
                rating=body.rating,
                company=body.company,
                mood_before=body.mood_before,
                mood_after=body.mood_after,
                custom_tags=body.custom_tags,
            ),
        )
    except FilmNotFoundError:
        raise HTTPException(status_code=404, detail='film not found') from None
    except MovieCardAlreadyExistsError:
        raise HTTPException(status_code=409, detail='movie card already exists') from None
    except MovieCardValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    tags = (
        (
            await db.execute(
                select(MovieCardTag.tag)
                .where(MovieCardTag.movie_card_id == card.id)
                .order_by(MovieCardTag.tag)
            )
        )
        .scalars()
        .all()
    )
    return CardResponse(
        id=card.id,
        film_id=card.film_id,
        rating=float(card.rating),
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=list(tags),
    )


@router.get(
    '/{card_id}', response_model=CardDetailResponse, summary='Получить карточку фильма по id'
)
async def get_card(
    card_id: int,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardDetailResponse:
    try:
        card = await GetMovieCardDetailsService(db).execute(card_id)
    except MovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return CardDetailResponse(
        id=card.id,
        film_id=card.film_id,
        film_kinopoisk_id=card.film_kinopoisk_id,
        film_genres=card.film_genres,
        film_title=card.film_title,
        film_year=card.film_year,
        film_poster_url=card.film_poster_url,
        rating=card.rating,
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=card.custom_tags,
    )


@router.get(
    '/{card_id}/comments',
    response_model=MovieCardCommentListResponse,
    summary='Получить комментарии карточки',
)
async def list_card_comments(
    card_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> MovieCardCommentListResponse:
    try:
        page = await ListMovieCardCommentsService(db).execute(
            card_id=card_id,
            parent_comment_id=None,
            cursor=cursor,
            limit=min(limit, 50),
            flat=True,
        )
    except ListCommentsMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return MovieCardCommentListResponse(
        items=[
            MovieCardCommentResponse(
                id=item.id,
                movie_card_id=item.movie_card_id,
                parent_comment_id=item.parent_comment_id,
                text=item.text,
                created_at=item.created_at,
                replies_count=item.replies_count,
                total_descendants_count=item.total_descendants_count,
                author=MovieCardCommentAuthorResponse(
                    id=item.author.id,
                    profile_slug=item.author.profile_slug,
                    username=item.author.username,
                    first_name=item.author.first_name,
                    last_name=item.author.last_name,
                    photo_url=item.author.photo_url,
                    display_name=item.author.display_name,
                ),
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{card_id}/comments/{comment_id}/replies',
    response_model=MovieCardCommentListResponse,
    summary='Получить ответы на комментарий',
)
async def list_card_comment_replies(
    card_id: int,
    comment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> MovieCardCommentListResponse:
    try:
        page = await ListMovieCardCommentsService(db).execute(
            card_id=card_id,
            parent_comment_id=comment_id,
            cursor=cursor,
            limit=min(limit, 50),
        )
    except ListCommentsMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail='comment not found') from None
    return MovieCardCommentListResponse(
        items=[
            MovieCardCommentResponse(
                id=item.id,
                movie_card_id=item.movie_card_id,
                parent_comment_id=item.parent_comment_id,
                text=item.text,
                created_at=item.created_at,
                replies_count=item.replies_count,
                total_descendants_count=item.total_descendants_count,
                author=MovieCardCommentAuthorResponse(
                    id=item.author.id,
                    profile_slug=item.author.profile_slug,
                    username=item.author.username,
                    first_name=item.author.first_name,
                    last_name=item.author.last_name,
                    photo_url=item.author.photo_url,
                    display_name=item.author.display_name,
                ),
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.post(
    '/{card_id}/comments',
    response_model=MovieCardCommentResponse,
    summary='Создать комментарий карточки',
)
async def create_card_comment(
    card_id: int,
    body: MovieCardCommentCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieCardCommentResponse:
    try:
        created = await CreateMovieCardCommentService(db).execute(
            card_id,
            user.id,
            CreateMovieCardCommentInput(
                text=body.text,
                parent_comment_id=body.parent_comment_id,
            ),
        )
    except CommentMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except ParentCommentNotFoundError:
        raise HTTPException(status_code=404, detail='parent comment not found') from None
    except ParentCommentMismatchError:
        raise HTTPException(
            status_code=422, detail='parent comment belongs to another card'
        ) from None
    except MovieCardCommentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return await _load_comment_response(db, created.id)
