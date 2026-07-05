from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from const.text_limits import WATCH_NOTE_MAX_LEN
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user_card import UserCard
from services.text.spoiler_tokens import (
    SpoilerTokenValidationError,
    validate_spoiler_tokens,
)
from services.user_card_categories.resolve_user_card_category_id_for_owner import (
    ResolveUserCardCategoryIdForOwnerService,
)


def _provider_from_meta(provider_meta: dict, card_id: str) -> str:
    provider = provider_meta.get('provider')
    if isinstance(provider, str) and provider.strip() != '':
        return provider.strip()
    if card_id.startswith('kp:'):
        return CatalogProvider.kinopoisk.value
    if card_id.startswith('rawg:'):
        return CatalogProvider.rawg.value
    if card_id.startswith('custom:'):
        return 'custom'
    return 'unknown'


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text != '' else None


def _normalize_watch_note(raw: str) -> str:
    s = (raw or '').strip()
    if len(s) > WATCH_NOTE_MAX_LEN:
        raise ValueError(f'watch note max length is {WATCH_NOTE_MAX_LEN}')
    try:
        return validate_spoiler_tokens(s)
    except SpoilerTokenValidationError as e:
        raise ValueError(str(e)) from e


@dataclass
class CreatePlannedUserCardService:
    """Creates or returns a planned UserCard used as the feed snippet for watchlist entries."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        user_id: UUID,
        card_id: str,
        provider_meta: dict,
        *,
        company: CardCompany = CardCompany.alone,
        category_id: int | None = None,
        watch_note: str = '',
    ) -> UserCard:
        provider = _provider_from_meta(provider_meta, card_id)
        data = provider_meta.get('data') or {}
        if not isinstance(data, dict):
            data = {}

        resolved_category_id = await ResolveUserCardCategoryIdForOwnerService.build(
            self._session
        ).execute(user_id, category_id)

        normalized_note = _normalize_watch_note(watch_note)

        if provider == CatalogProvider.kinopoisk.value:
            return await self._upsert_kinopoisk(
                user_id,
                card_id,
                data,
                resolved_category_id,
                company,
                normalized_note,
            )
        if provider == CatalogProvider.rawg.value:
            return await self._upsert_rawg(
                user_id,
                card_id,
                data,
                resolved_category_id,
                company,
                normalized_note,
            )
        return await self._upsert_custom(
            user_id,
            card_id,
            data,
            resolved_category_id,
            company,
            normalized_note,
        )

    def _apply_planned_fields(
        self,
        entity: UserCard,
        *,
        category_id: int,
        company: CardCompany,
        watch_note: str,
    ) -> UserCard:
        entity.category_id = category_id
        entity.company = company.value
        entity.watch_note = watch_note
        return entity

    async def _find_planned(
        self,
        user_id: UUID,
        *,
        film_id: int | None = None,
        catalog_item_id: int | None = None,
        provider: CatalogProvider | None = None,
        external_id: str | None = None,
        display_title: str | None = None,
    ) -> UserCard | None:
        stmt = select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.is_planned.is_(True),
        )
        if film_id is not None:
            stmt = stmt.where(UserCard.film_id == film_id)
        elif catalog_item_id is not None:
            stmt = stmt.where(UserCard.catalog_item_id == catalog_item_id)
        elif provider is not None and external_id is not None:
            stmt = stmt.where(
                UserCard.provider == provider,
                UserCard.external_id == external_id,
            )
        elif display_title is not None:
            stmt = stmt.where(
                UserCard.provider == CatalogProvider.no_provider,
                UserCard.display_title == display_title,
            )
        else:
            return None
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _upsert_kinopoisk(
        self,
        user_id: UUID,
        card_id: str,
        data: dict,
        category_id: int,
        company: CardCompany,
        watch_note: str,
    ) -> UserCard:
        kp_raw = data.get('kp_id')
        kp_id = int(kp_raw) if kp_raw is not None else int(card_id.removeprefix('kp:'))
        external_id = str(kp_id)

        film = (
            await self._session.execute(select(Film).where(Film.kinopoisk_id == kp_id))
        ).scalar_one_or_none()

        film_id: int | None = int(film.id) if film is not None else None
        catalog_item_id: int | None = None
        if film_id is not None:
            ci_id = (
                await self._session.execute(
                    select(CatalogItem.id).where(CatalogItem.film_id == film_id)
                )
            ).scalar_one_or_none()
            if ci_id is not None:
                catalog_item_id = int(ci_id)

        existing = await self._find_planned(
            user_id,
            film_id=film_id,
            catalog_item_id=catalog_item_id if film_id is None else None,
            provider=CatalogProvider.kinopoisk if film_id is None else None,
            external_id=external_id if film_id is None else None,
        )
        if existing is not None:
            self._apply_planned_fields(
                existing,
                category_id=category_id,
                company=company,
                watch_note=watch_note,
            )
            await self._session.flush()
            return existing

        entity = UserCard(
            user_id=user_id,
            film_id=film_id,
            catalog_item_id=catalog_item_id,
            category_id=category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=external_id,
            rating=0.0,
            company=company.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note=watch_note,
            is_planned=True,
        )
        if film is not None:
            entity.display_title = film.title
            entity.display_cover_url = film.poster_url
            sd = film.short_description or film.description
            entity.display_summary = sd
        else:
            entity.display_title = str(data.get('title') or f'Kinopoisk #{kp_id}')
            entity.display_cover_url = _optional_str(
                data.get('poster_url') or data.get('display_cover_url')
            )
            entity.display_summary = _optional_str(data.get('description'))

        return await self._persist(entity)

    async def _upsert_rawg(
        self,
        user_id: UUID,
        card_id: str,
        data: dict,
        category_id: int,
        company: CardCompany,
        watch_note: str,
    ) -> UserCard:
        slug = data.get('slug') or data.get('external_id')
        if not isinstance(slug, str) or slug.strip() == '':
            slug = card_id.removeprefix('rawg:') if card_id.startswith('rawg:') else None
        external_id = str(slug) if slug is not None else None

        catalog_item_id: int | None = None
        ci_id_raw = data.get('catalog_item_id')
        if ci_id_raw is not None:
            catalog_item_id = int(ci_id_raw)
        elif external_id is not None:
            ci = (
                await self._session.execute(
                    select(CatalogItem).where(
                        CatalogItem.provider == CatalogProvider.rawg,
                        CatalogItem.external_id == external_id,
                    )
                )
            ).scalar_one_or_none()
            if ci is not None:
                catalog_item_id = int(ci.id)

        existing = await self._find_planned(
            user_id,
            catalog_item_id=catalog_item_id,
            provider=CatalogProvider.rawg if catalog_item_id is None else None,
            external_id=external_id if catalog_item_id is None else None,
        )
        if existing is not None:
            self._apply_planned_fields(
                existing,
                category_id=category_id,
                company=company,
                watch_note=watch_note,
            )
            await self._session.flush()
            return existing

        ci: CatalogItem | None = None
        if catalog_item_id is not None:
            ci = await self._session.get(CatalogItem, catalog_item_id)

        film_id: int | None = int(ci.film_id) if ci is not None and ci.film_id is not None else None
        provider = ci.provider if ci is not None else CatalogProvider.rawg
        resolved_external_id = ci.external_id if ci is not None else external_id

        entity = UserCard(
            user_id=user_id,
            film_id=film_id,
            catalog_item_id=catalog_item_id,
            category_id=category_id,
            provider=provider,
            external_id=resolved_external_id,
            rating=0.0,
            company=company.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note=watch_note,
            is_planned=True,
        )

        if ci is not None and ci.film_id is not None:
            film = await self._session.get(Film, ci.film_id)
            if film is not None:
                entity.display_title = film.title
                entity.display_cover_url = film.poster_url
                entity.display_summary = film.short_description or film.description
        elif ci is not None and ci.game_id is not None:
            game = await self._session.get(Game, ci.game_id)
            if game is not None:
                entity.display_title = str(game.name or data.get('title') or external_id or 'Game')
                entity.display_cover_url = game.background_image
        else:
            entity.display_title = str(data.get('title') or external_id or card_id)
            entity.display_cover_url = _optional_str(
                data.get('poster_url') or data.get('display_cover_url')
            )
            entity.display_summary = _optional_str(data.get('description'))

        return await self._persist(entity)

    async def _upsert_custom(
        self,
        user_id: UUID,
        card_id: str,
        data: dict,
        category_id: int,
        company: CardCompany,
        watch_note: str,
    ) -> UserCard:
        title = str(
            data.get('title') or data.get('display_title') or card_id.removeprefix('custom:')
        )
        existing = await self._find_planned(user_id, display_title=title)
        if existing is not None:
            self._apply_planned_fields(
                existing,
                category_id=category_id,
                company=company,
                watch_note=watch_note,
            )
            await self._session.flush()
            return existing

        entity = UserCard(
            user_id=user_id,
            film_id=None,
            catalog_item_id=None,
            category_id=category_id,
            provider=CatalogProvider.no_provider,
            external_id=None,
            rating=0.0,
            company=company.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note=watch_note,
            is_planned=True,
            display_title=title,
            display_cover_url=_optional_str(
                data.get('poster_url') or data.get('display_cover_url')
            ),
            display_summary=_optional_str(data.get('description')),
            source_url=card_id,
        )
        return await self._persist(entity)

    async def _persist(self, entity: UserCard) -> UserCard:
        try:
            async with self._session.begin_nested():
                self._session.add(entity)
                await self._session.flush()
        except IntegrityError:
            if entity.film_id is not None:
                found = await self._find_planned(entity.user_id, film_id=entity.film_id)
            elif entity.catalog_item_id is not None:
                found = await self._find_planned(
                    entity.user_id,
                    catalog_item_id=entity.catalog_item_id,
                )
            elif entity.external_id is not None:
                found = await self._find_planned(
                    entity.user_id,
                    provider=entity.provider,
                    external_id=entity.external_id,
                )
            else:
                found = await self._find_planned(
                    entity.user_id,
                    display_title=entity.display_title,
                )
            if found is not None:
                return found
            raise
        return entity
