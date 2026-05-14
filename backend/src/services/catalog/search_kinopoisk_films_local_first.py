from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.kinopoisk.kinopoisk_search_dto import (
    KinopoiskFilmSearchItemDTO,
    genres_for_film_model,
)
from services.catalog.ttl_coalescing_cache import KINOPOISK_FILM_SEARCH_CACHE

PAGE_SIZE: int = 20


def _normalize_keyword(keyword: str) -> str:
    return ' '.join(keyword.strip().split())


def _ilike_pattern(keyword: str) -> str:
    safe = _normalize_keyword(keyword).replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{safe}%'


def _subtitle(year: int | None, film_kind: str | None) -> str | None:
    parts: list[str] = []
    if year is not None:
        parts.append(str(year))
    if film_kind:
        parts.append(film_kind)
    if not parts:
        return None
    return ' · '.join(parts)


@dataclass(frozen=True, slots=True)
class CatalogFilmSearchHitDTO:
    """Normalized Kinopoisk-backed film hit for catalog search UIs."""

    provider: CatalogProvider
    external_id: str
    kinopoisk_id: int
    title: str
    subtitle: str | None
    cover_url: str | None
    summary: str | None
    film_id: int
    catalog_item_id: int | None
    source: Literal['local', 'provider']


@dataclass(frozen=True, slots=True)
class SearchKinopoiskFilmsResult:
    keyword: str
    page: int
    pages_count: int
    total_remote: int
    hits: tuple[CatalogFilmSearchHitDTO, ...]
    has_more: bool


@dataclass
class SearchKinopoiskFilmsLocalFirstService:
    """Keyword search for films with DB matches first, then Kinopoisk search API for gaps.

    Persists provider rows as ``Film`` + ``CatalogItem(provider=kinopoisk, external_id, film_id)`` so
    resolve and card flows stay aligned with catalog identities.
    """

    _session: AsyncSession
    _transport: KinopoiskProviderTransport

    @classmethod
    def build(
        cls,
        session: AsyncSession,
        *,
        transport: KinopoiskProviderTransport | None = None,
    ) -> Self:
        return cls(
            _session=session,
            _transport=transport or KinopoiskProviderTransport(),
        )

    async def execute(
        self,
        keyword: str,
        *,
        page: int = 1,
    ) -> SearchKinopoiskFilmsResult:
        norm = _normalize_keyword(keyword)
        if not norm:
            return SearchKinopoiskFilmsResult(
                keyword='',
                page=max(1, page),
                pages_count=0,
                total_remote=0,
                hits=(),
                has_more=False,
            )

        page = max(1, page)
        return await KINOPOISK_FILM_SEARCH_CACHE.get_or_fetch(
            f'kinopoisk:film_search:{norm}:{page}',
            lambda: self._execute_impl(norm, page),
        )

    async def _execute_impl(self, norm: str, page: int) -> SearchKinopoiskFilmsResult:
        local_hits: list[CatalogFilmSearchHitDTO] = []
        seen_kp: set[int] = set()

        if page == 1:
            local_films = await self._load_local_films(norm)
            for film in local_films[:PAGE_SIZE]:
                hit = await self._hit_from_local_film(film)
                local_hits.append(hit)
                seen_kp.add(film.kinopoisk_id)

        skip_remote = page == 1 and len(local_hits) >= PAGE_SIZE

        if skip_remote:
            return SearchKinopoiskFilmsResult(
                keyword=norm,
                page=page,
                pages_count=1,
                total_remote=len(local_hits),
                hits=tuple(local_hits),
                has_more=False,
            )

        remote = await self._transport.search_films_by_keyword(norm, page=page)
        merged = list(local_hits)

        if page > 1:
            merged = []
            seen_kp = set()

        for item in remote.films:
            if item.kinopoisk_id in seen_kp:
                continue
            film, catalog_item = await self._upsert_film_and_catalog_from_search_item(item)
            merged.append(self._hit_from_provider_row(film, item, catalog_item))
            seen_kp.add(item.kinopoisk_id)
            if page == 1 and len(merged) >= PAGE_SIZE:
                break

        kw_out = remote.keyword or norm
        has_more = page < remote.pages_count
        return SearchKinopoiskFilmsResult(
            keyword=kw_out,
            page=page,
            pages_count=max(1, remote.pages_count),
            total_remote=remote.search_films_count_result,
            hits=tuple(merged),
            has_more=has_more,
        )

    async def _load_local_films(self, norm: str) -> list[Film]:
        pattern = _ilike_pattern(norm)
        result = await self._session.execute(
            select(Film)
            .where(Film.title.ilike(pattern, escape='\\'))
            .order_by(Film.title.asc())
            .limit(PAGE_SIZE * 3),
        )
        return list(result.scalars().all())

    async def _hit_from_local_film(self, film: Film) -> CatalogFilmSearchHitDTO:
        cat = await self._ensure_kinopoisk_catalog_item(film)
        return CatalogFilmSearchHitDTO(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            kinopoisk_id=film.kinopoisk_id,
            title=film.title,
            subtitle=_subtitle(film.year, None),
            cover_url=film.poster_url,
            summary=film.short_description,
            film_id=film.id,
            catalog_item_id=cat.id,
            source='local',
        )

    def _hit_from_provider_row(
        self,
        film: Film,
        item: KinopoiskFilmSearchItemDTO,
        catalog_item: CatalogItem,
    ) -> CatalogFilmSearchHitDTO:
        title = item.display_title() or film.title
        summary = item.description.strip() if item.description and item.description.strip() else None
        return CatalogFilmSearchHitDTO(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            kinopoisk_id=film.kinopoisk_id,
            title=title,
            subtitle=_subtitle(item.year_as_int(), item.film_kind),
            cover_url=item.poster_url_normalized() or film.poster_url,
            summary=summary,
            film_id=film.id,
            catalog_item_id=catalog_item.id,
            source='provider',
        )

    async def _ensure_kinopoisk_catalog_item(self, film: Film) -> CatalogItem:
        external_id = str(film.kinopoisk_id)
        existing = (
            await self._session.execute(
                select(CatalogItem).where(
                    CatalogItem.provider == CatalogProvider.kinopoisk,
                    CatalogItem.external_id == external_id,
                ),
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.film_id != film.id:
                existing.film_id = film.id
                await self._session.commit()
                await self._session.refresh(existing)
            return existing

        item = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=external_id,
            film_id=film.id,
        )
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def _upsert_film_and_catalog_from_search_item(
        self,
        item: KinopoiskFilmSearchItemDTO,
    ) -> tuple[Film, CatalogItem]:
        title = item.display_title()
        if title == '':
            title = f'kinopoisk:{item.kinopoisk_id}'

        existing = (
            await self._session.execute(select(Film).where(Film.kinopoisk_id == item.kinopoisk_id))
        ).scalar_one_or_none()
        year = item.year_as_int()
        poster = item.poster_url_normalized()
        genres = genres_for_film_model(item)
        summary_text = item.description.strip() if item.description and item.description.strip() else None

        if existing is not None:
            existing.title = title
            existing.year = year
            existing.poster_url = poster
            existing.genres = genres
            if summary_text is not None:
                existing.short_description = summary_text
        else:
            existing = Film(
                kinopoisk_id=item.kinopoisk_id,
                title=title,
                year=year,
                poster_url=poster,
                genres=genres,
                short_description=summary_text,
                description=None,
            )
            self._session.add(existing)

        await self._session.commit()
        await self._session.refresh(existing)

        cat = await self._ensure_kinopoisk_catalog_item(existing)
        return existing, cat


__all__ = (
    'PAGE_SIZE',
    'CatalogFilmSearchHitDTO',
    'SearchKinopoiskFilmsLocalFirstService',
    'SearchKinopoiskFilmsResult',
)
