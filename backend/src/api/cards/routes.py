from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.schemas import CardCreateRequest, CardDetailResponse, CardResponse
from core.database import get_db
from deps.auth import CurrentUser
from models.movie_card_tag import MovieCardTag
from services.cards.create_movie_card import (
    CreateMovieCardInput,
    CreateMovieCardService,
    FilmNotFoundError,
    MovieCardAlreadyExistsError,
    MovieCardValidationError,
)
from services.cards.get_movie_card_details import GetMovieCardDetailsService, MovieCardNotFoundError

router = APIRouter(prefix='/cards', tags=['cards'])


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


@router.get('/{card_id}', response_model=CardDetailResponse, summary='Получить карточку фильма по id')
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
        film_title=card.film_title,
        film_year=card.film_year,
        film_poster_url=card.film_poster_url,
        rating=card.rating,
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=card.custom_tags,
    )
