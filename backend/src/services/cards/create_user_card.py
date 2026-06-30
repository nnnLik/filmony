from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from math import isfinite
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.card_tag import CardTag
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user_card import UserCard
from models.watchlist_entry import WatchlistEntry
from services.user_card_categories.resolve_user_card_category_id_for_owner import (
    ResolveUserCardCategoryIdForOwnerService,
)


class FilmNotFoundError(Exception):
    pass


class CatalogItemNotFoundError(Exception):
    pass


class UserCardAlreadyExistsError(Exception):
    pass


class UserCardValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateUserCardInput:
    rating: float
    company: CardCompany
    mood_before: CardMoodBefore
    mood_after: CardMoodAfter
    custom_tags: Sequence[str]
    watch_note: str
    film_id: int | None = None
    kinopoisk_id: int | None = None
    catalog_item_id: int | None = None
    provider: CatalogProvider | None = None
    external_id: str | None = None
    genres: Sequence[str] = ()
    display_title: str | None = None
    display_cover_url: str | None = None
    display_summary: str | None = None
    category_id: int | None = None


def _normalize_rating(value: float) -> float:
    if not isfinite(value):
        raise UserCardValidationError('rating must be finite')
    snapped = round(value * 2) / 2
    if abs(snapped - value) > 1e-8:
        raise UserCardValidationError('rating must have 0.5 step')
    if snapped < 1 or snapped > 10:
        raise UserCardValidationError('rating must be in [1, 10]')
    return snapped


def _normalize_tags(tags: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip()
        if tag == '':
            continue
        if len(tag) > 40:
            raise UserCardValidationError('custom tag max length is 40')
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    if len(normalized) > 5:
        raise UserCardValidationError('max 5 custom tags allowed')
    return normalized


def _normalize_watch_note(raw: str) -> str:
    s = (raw or '').strip()
    if len(s) > 500:
        raise UserCardValidationError('watch note max length is 500')
    return s


def _normalize_genres(genres: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in genres:
        genre = raw.strip()
        if genre == '':
            continue
        if len(genre) > 80:
            raise UserCardValidationError('genre max length is 80')
        key = genre.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(genre)
    if len(normalized) > 20:
        raise UserCardValidationError('max 20 genres allowed')
    return normalized


def _normalize_catalog_external_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if s == '':
        return None
    if len(s) > 255:
        raise UserCardValidationError('external_id max length is 255')
    return s


def _normalize_display_summary(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if len(s) > 8000:
        raise UserCardValidationError('display_summary max length is 8000')
    return s or None


def _normalize_optional_url(raw: str | None, *, field: str) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == '':
        return None
    if len(s) > 2048:
        raise UserCardValidationError(f'{field} max length is 2048')
    return s


def _apply_display_from_film(entity: UserCard, film: Film) -> None:
    entity.display_title = film.title
    entity.display_cover_url = film.poster_url
    sd = film.short_description or film.description
    entity.display_summary = sd


def _watchlist_card_id_for_provider(provider: CatalogProvider, external_id: str) -> str:
    if provider == CatalogProvider.kinopoisk:
        return f'kp:{external_id}'
    return f'{provider.value}:{external_id}'


class CreateUserCardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: CreateUserCardInput) -> UserCard:
        rating = _normalize_rating(payload.rating)
        custom_tags = _normalize_tags(payload.custom_tags)
        watch_note = _normalize_watch_note(payload.watch_note)
        genres = _normalize_genres(payload.genres)
        cover_url = _normalize_optional_url(payload.display_cover_url, field='display_cover_url')
        summary = _normalize_display_summary(payload.display_summary)
        try:
            resolved_category_id = await ResolveUserCardCategoryIdForOwnerService.build(
                self._session
            ).execute(user_id, payload.category_id)
        except ResolveUserCardCategoryIdForOwnerService.CategoryNotFoundForUserError as e:
            raise UserCardValidationError('category not found') from e

        ext_norm = _normalize_catalog_external_id(payload.external_id)
        has_film = payload.film_id is not None
        has_catalog = payload.catalog_item_id is not None
        manual_title = (payload.display_title or '').strip()

        has_ke = payload.provider == CatalogProvider.kinopoisk and ext_norm is not None

        if payload.provider == CatalogProvider.no_provider:
            if ext_norm is not None:
                raise UserCardValidationError('external_id must not be set for no_provider')
            if has_film or has_catalog or has_ke:
                raise UserCardValidationError(
                    'no_provider cannot be combined with film_id, catalog_item_id, '
                    'or kinopoisk external_id',
                )
            if not manual_title:
                raise UserCardValidationError('display_title is required for no_provider')

        if (
            payload.provider == CatalogProvider.kinopoisk
            and not has_ke
            and not has_film
            and not has_catalog
        ):
            raise UserCardValidationError(
                'provider kinopoisk requires external_id, '
                'or omit provider and use film_id/catalog_item_id',
            )

        if ext_norm is not None:
            if payload.provider not in (None, CatalogProvider.kinopoisk):
                raise UserCardValidationError('external_id is only valid with provider kinopoisk')
            if payload.provider is None:
                raise UserCardValidationError(
                    'provider kinopoisk is required when external_id is set'
                )

        is_manual = not has_film and not has_catalog and not has_ke and bool(manual_title)

        modes = int(has_film) + int(has_catalog) + int(has_ke) + int(is_manual)
        if modes != 1:
            raise UserCardValidationError(
                'exactly one of: film-backed (film_id), catalog_item_id, '
                'kinopoisk external subject (provider kinopoisk + external_id), '
                'or display_title (manual)',
            )

        if has_film:
            return await self._create_film_backed(
                user_id,
                resolved_category_id,
                rating,
                custom_tags,
                watch_note,
                genres,
                payload,
                cover_url,
                summary,
            )
        if has_catalog:
            return await self._create_catalog_backed(
                user_id,
                resolved_category_id,
                rating,
                custom_tags,
                watch_note,
                genres,
                payload,
                cover_url,
                summary,
            )
        if has_ke:
            assert ext_norm is not None
            ci = (
                await self._session.execute(
                    select(CatalogItem).where(
                        CatalogItem.provider == CatalogProvider.kinopoisk,
                        CatalogItem.external_id == ext_norm,
                    )
                )
            ).scalar_one_or_none()
            if ci is None:
                raise CatalogItemNotFoundError
            bridged = replace(
                payload,
                catalog_item_id=int(ci.id),
                film_id=None,
                kinopoisk_id=None,
                provider=None,
                external_id=None,
            )
            return await self._create_catalog_backed(
                user_id,
                resolved_category_id,
                rating,
                custom_tags,
                watch_note,
                genres,
                bridged,
                cover_url,
                summary,
            )
        return await self._create_manual(
            user_id,
            resolved_category_id,
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
        category_id: int,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        genres: list[str],
        payload: CreateUserCardInput,
        display_cover_url: str | None,
        display_summary: str | None,
    ) -> UserCard:
        assert payload.film_id is not None
        if payload.kinopoisk_id is None:
            raise UserCardValidationError('kinopoisk_id is required with film_id')

        film_result = await self._session.execute(select(Film).where(Film.id == payload.film_id))
        film = film_result.scalar_one_or_none()
        if film is None:
            raise FilmNotFoundError
        if film.kinopoisk_id != payload.kinopoisk_id:
            raise UserCardValidationError('kinopoisk_id does not match film_id')
        if genres != (film.genres or []):
            film.genres = genres

        ci_id = (
            await self._session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == payload.film_id)
            )
        ).scalar_one_or_none()

        entity = UserCard(
            user_id=user_id,
            film_id=payload.film_id,
            catalog_item_id=int(ci_id) if ci_id is not None else None,
            category_id=category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
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
            raise UserCardAlreadyExistsError from exc

        await self._session.execute(
            delete(WatchlistEntry).where(
                WatchlistEntry.user_id == user_id,
                WatchlistEntry.card_id == f'kp:{payload.kinopoisk_id}',
            )
        )

        if custom_tags:
            self._session.add_all([CardTag(card_id=entity.id, tag=tag) for tag in custom_tags])
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def _create_catalog_backed(
        self,
        user_id: UUID,
        category_id: int,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        genres: list[str],
        payload: CreateUserCardInput,
        display_cover_url: str | None,
        display_summary: str | None,
    ) -> UserCard:
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

        entity = UserCard(
            user_id=user_id,
            film_id=ci.film_id,
            catalog_item_id=ci.id,
            category_id=category_id,
            provider=ci.provider,
            external_id=ci.external_id,
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
                raise UserCardValidationError('display_title is required for this catalog item')
            if len(mt) > 255:
                raise UserCardValidationError('display_title max length is 255')
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
            raise UserCardAlreadyExistsError from exc

        if ci.external_id is not None:
            await self._session.execute(
                delete(WatchlistEntry).where(
                    WatchlistEntry.user_id == user_id,
                    WatchlistEntry.card_id
                    == _watchlist_card_id_for_provider(ci.provider, ci.external_id),
                )
            )

        if custom_tags:
            self._session.add_all([CardTag(card_id=entity.id, tag=tag) for tag in custom_tags])
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def _create_manual(
        self,
        user_id: UUID,
        category_id: int,
        rating: float,
        custom_tags: list[str],
        watch_note: str,
        title: str,
        display_cover_url: str | None,
        display_summary: str | None,
        company: CardCompany,
        mood_before: CardMoodBefore,
        mood_after: CardMoodAfter,
    ) -> UserCard:
        if len(title) > 255:
            raise UserCardValidationError('display_title max length is 255')

        entity = UserCard(
            user_id=user_id,
            film_id=None,
            catalog_item_id=None,
            category_id=category_id,
            provider=CatalogProvider.no_provider,
            external_id=None,
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
            raise UserCardAlreadyExistsError from exc

        if custom_tags:
            self._session.add_all([CardTag(card_id=entity.id, tag=tag) for tag in custom_tags])
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
