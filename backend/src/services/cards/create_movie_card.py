from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.movie_card_tag import MovieCardTag
from models.user_watchlist_film import UserWatchlistFilm


class FilmNotFoundError(Exception):
    pass


class CatalogItemNotFoundError(Exception):
    pass


class MovieCardAlreadyExistsError(Exception):
    pass


class MovieCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateMovieCardInput:
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: Sequence[str]
    watch_note: str
    film_id: int | None = None
    kinopoisk_id: int | None = None
    catalog_item_id: int | None = None
    genres: Sequence[str] = ()
    display_title: str | None = None
    display_cover_url: str | None = None
    display_summary: str | None = None


def _normalize_rating(value: float) -> float:
    if not isfinite(value):
        raise MovieCardValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise MovieCardValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise MovieCardValidationError('rating must be in [1, 10]')
    return snapped


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip()
        if tag == '':
            continue
        if len(tag) > 40:
            raise MovieCardValidationError('custom tag max length is 40')
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    if len(normalized) > 5:
        raise MovieCardValidationError('max 5 custom tags allowed')
    return normalized


def _normalize_watch_note(raw: str) -> str:
    s = (raw or '').strip()
    if len(s) > 500:
        raise MovieCardValidationError('watch note max length is 500')
    return s


def _normalize_genres(genres: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in genres:
        genre = raw.strip()
        if genre == '':
            continue
        if len(genre) > 80:
            raise MovieCardValidationError('genre max length is 80')
        key = genre.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(genre)
    if len(normalized) > 20:
        raise MovieCardValidationError('max 20 genres allowed')
    return normalized


def _normalize_display_summary(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if len(s) > 8000:
        raise MovieCardValidationError('display_summary max length is 8000')
    return s or None


def _normalize_optional_url(raw: str | None, *, field: str) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == '':
        return None
    if len(s) > 2048:
        raise MovieCardValidationError(f'{field} max length is 2048')
    return s


def _apply_display_from_film(entity: MovieCard, film: Film) -> None:
    entity.display_title = film.title
    entity.display_cover_url = film.poster_url
    sd = film.short_description or film.description
    entity.display_summary = sd


class CreateMovieCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: CreateMovieCardInput) -> MovieCard:
        rating = _normalize_rating(payload.rating)
        custom_tags = _normalize_tags(payload.custom_tags)
        watch_note = _normalize_watch_note(payload.watch_note)
        genres = _normalize_genres(payload.genres)
        cover_url = _normalize_optional_url(payload.display_cover_url, field='display_cover_url')
        summary = _normalize_display_summary(payload.display_summary)

        has_film = payload.film_id is not None
        has_catalog = payload.catalog_item_id is not None
        manual_title = (payload.display_title or '').strip()

        is_manual = not has_film and not has_catalog and bool(manual_title)
        modes = int(has_film) + int(has_catalog) + int(is_manual)
        if modes != 1:
            raise MovieCardValidationError(
                'exactly one of: film-backed (film_id), catalog_item_id, or display_title (manual)',
            )

        if has_film:
            return await self._create_film_backed(
                user_id, rating, custom_tags, watch_note, genres, payload, cover_url, summary
            )
        if has_catalog:
            return await self._create_catalog_backed(
                user_id, rating, custom_tags, watch_note, genres, payload, cover_url, summary
            )
        return await self._create_manual(
            user_id,
            rating,
            custom_tags,
            watch_note,
            manual_title,
            cover_url,
            summary,
            payload.company,
            payload.mood_before,
            payload.mood_after,
        )

    async def _create_film_backed(
        self,
        user_id: UUID,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        genres: list[str],
        payload: CreateMovieCardInput,
        display_cover_url: str | None,
        display_summary: str | None,
    ) -> MovieCard:
        assert payload.film_id is not None
        if payload.kinopoisk_id is None:
            raise MovieCardValidationError('kinopoisk_id is required with film_id')

        film_result = await self._session.execute(select(Film).where(Film.id == payload.film_id))
        film = film_result.scalar_one_or_none()
        if film is None:
            raise FilmNotFoundError
        if film.kinopoisk_id != payload.kinopoisk_id:
            raise MovieCardValidationError('kinopoisk_id does not match film_id')
        if genres != (film.genres or []):
            film.genres = genres

        ci_id = (
            await self._session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == payload.film_id)
            )
        ).scalar_one_or_none()

        entity = MovieCard(
            user_id=user_id,
            film_id=payload.film_id,
            catalog_item_id=int(ci_id) if ci_id is not None else None,
            rating=rating,
            company=payload.company.value,
            mood_before=payload.mood_before.value,
            mood_after=payload.mood_after.value,
            watch_note=watch_note,
        )
        _apply_display_from_film(entity, film)
        if display_cover_url is not None:
            entity.display_cover_url = display_cover_url
        if display_summary is not None:
            entity.display_summary = display_summary

        self._session.add(entity)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise MovieCardAlreadyExistsError from exc

        await self._session.execute(
            delete(UserWatchlistFilm).where(
                UserWatchlistFilm.user_id == user_id,
                UserWatchlistFilm.film_id == payload.film_id,
            )
        )

        if custom_tags:
            self._session.add_all(
                [MovieCardTag(movie_card_id=entity.id, tag=tag) for tag in custom_tags]
            )
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def _create_catalog_backed(
        self,
        user_id: UUID,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        genres: list[str],
        payload: CreateMovieCardInput,
        display_cover_url: str | None,
        display_summary: str | None,
    ) -> MovieCard:
        assert payload.catalog_item_id is not None
        ci = (
            await self._session.execute(
                select(CatalogItem).where(CatalogItem.id == payload.catalog_item_id)
            )
        ).scalar_one_or_none()
        if ci is None:
            raise CatalogItemNotFoundError

        film: Film | None = None
        if ci.film_id is not None:
            film = (
                await self._session.execute(select(Film).where(Film.id == ci.film_id))
            ).scalar_one_or_none()
            if film is None:
                raise FilmNotFoundError
            if genres != (film.genres or []):
                film.genres = genres

        entity = MovieCard(
            user_id=user_id,
            film_id=ci.film_id,
            catalog_item_id=ci.id,
            rating=rating,
            company=payload.company.value,
            mood_before=payload.mood_before.value,
            mood_after=payload.mood_after.value,
            watch_note=watch_note,
        )
        if film is not None:
            _apply_display_from_film(entity, film)
        else:
            mt = (payload.display_title or '').strip()
            if not mt:
                raise MovieCardValidationError('display_title is required for this catalog item')
            if len(mt) > 255:
                raise MovieCardValidationError('display_title max length is 255')
            entity.display_title = mt
            entity.display_cover_url = display_cover_url
            entity.display_summary = display_summary

        if film is not None:
            if display_cover_url is not None:
                entity.display_cover_url = display_cover_url
            if display_summary is not None:
                entity.display_summary = display_summary

        self._session.add(entity)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise MovieCardAlreadyExistsError from exc

        if film is not None:
            await self._session.execute(
                delete(UserWatchlistFilm).where(
                    UserWatchlistFilm.user_id == user_id,
                    UserWatchlistFilm.film_id == film.id,
                )
            )

        if custom_tags:
            self._session.add_all(
                [MovieCardTag(movie_card_id=entity.id, tag=tag) for tag in custom_tags]
            )
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def _create_manual(
        self,
        user_id: UUID,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        title: str,
        display_cover_url: str | None,
        display_summary: str | None,
        company: CardCompany,
        mood_before: CardMoodBefore,
        mood_after: CardMoodAfter,
    ) -> MovieCard:
        if len(title) > 255:
            raise MovieCardValidationError('display_title max length is 255')

        entity = MovieCard(
            user_id=user_id,
            film_id=None,
            catalog_item_id=None,
            rating=rating,
            company=company.value,
            mood_before=mood_before.value,
            mood_after=mood_after.value,
            watch_note=watch_note,
            display_title=title,
            display_cover_url=display_cover_url,
            display_summary=display_summary,
        )

        self._session.add(entity)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise MovieCardAlreadyExistsError from exc

        if custom_tags:
            self._session.add_all(
                [MovieCardTag(movie_card_id=entity.id, tag=tag) for tag in custom_tags]
            )
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
