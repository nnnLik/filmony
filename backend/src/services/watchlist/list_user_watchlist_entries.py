from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.watchlist_entry import WatchlistEntry

_CURSOR_PREFIX = 'wle1'


def _encode_cursor(created_at: dt.datetime, entry_id: int) -> str:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=dt.UTC)
    us = int(created_at.timestamp() * 1_000_000)
    return f'{_CURSOR_PREFIX}.{us}.{entry_id}'


def _decode_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.split('.')
    if len(parts) != 3 or parts[0] != _CURSOR_PREFIX:
        return None
    try:
        us = int(parts[1], 10)
        entry_id = int(parts[2], 10)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(us / 1_000_000, tz=dt.UTC), entry_id


def _provider_from_entry(entry: WatchlistEntry) -> str:
    meta = entry.provider_meta or {}
    provider = meta.get('provider')
    if isinstance(provider, str) and provider.strip() != '':
        return provider.strip()
    if entry.card_id.startswith('kp:'):
        return CatalogProvider.kinopoisk.value
    if entry.card_id.startswith('rawg:'):
        return CatalogProvider.rawg.value
    if entry.card_id.startswith('custom:'):
        return 'custom'
    return 'unknown'


def _year_from_released(released: str | None) -> int | None:
    if released is None or released.strip() == '':
        return None
    match = re.match(r'^(\d{4})', released.strip())
    if match is None:
        return None
    return int(match.group(1))


@dataclass(frozen=True, slots=True)
class WatchlistEntryListItem:
    entry_id: int
    card_id: str
    provider: str
    title: str
    poster_url: str | None
    year: int | None
    watch_tag: str
    watch_with_user_id: UUID | None
    created_at: dt.datetime
    film_id: int | None = None
    film_kinopoisk_id: int | None = None
    film_genres: list[str] | None = None
    catalog_item_id: int | None = None
    external_id: str | None = None


@dataclass(frozen=True, slots=True)
class WatchlistEntryPage:
    items: list[WatchlistEntryListItem]
    next_cursor: str | None


@dataclass
class ListUserWatchlistEntriesService:
    """Returns provider-aware watchlist entries for a user's public «Позже» list."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
    ) -> WatchlistEntryPage:
        cursor_ts: dt.datetime | None = None
        cursor_id: int | None = None
        if cursor is not None and cursor.strip() != '':
            decoded = _decode_cursor(cursor.strip())
            if decoded is None:
                raise self.InvalidCursor
            cursor_ts, cursor_id = decoded

        cap = max(1, min(limit, 50))
        where_parts = [WatchlistEntry.user_id == user_id]
        if cursor_ts is not None and cursor_id is not None:
            where_parts.append(
                or_(
                    WatchlistEntry.created_at < cursor_ts,
                    and_(WatchlistEntry.created_at == cursor_ts, WatchlistEntry.id < cursor_id),
                )
            )

        stmt = (
            select(WatchlistEntry)
            .where(and_(*where_parts))
            .order_by(WatchlistEntry.created_at.desc(), WatchlistEntry.id.desc())
            .limit(cap + 1)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_more = len(rows) > cap
        slice_rows = rows[:cap] if has_more else rows
        if not slice_rows:
            return WatchlistEntryPage(items=[], next_cursor=None)

        kp_ids: set[int] = set()
        rawg_external_ids: set[str] = set()
        catalog_item_ids: set[int] = set()

        for entry in slice_rows:
            provider = _provider_from_entry(entry)
            data = (entry.provider_meta or {}).get('data') or {}
            if provider == CatalogProvider.kinopoisk.value:
                kp_raw = data.get('kp_id')
                if kp_raw is not None:
                    kp_ids.add(int(kp_raw))
                elif entry.card_id.startswith('kp:'):
                    kp_ids.add(int(entry.card_id.removeprefix('kp:')))
            elif provider == CatalogProvider.rawg.value:
                slug = data.get('slug') or data.get('external_id')
                if isinstance(slug, str) and slug.strip() != '':
                    rawg_external_ids.add(slug.strip())
                elif entry.card_id.startswith('rawg:'):
                    rawg_external_ids.add(entry.card_id.removeprefix('rawg:'))
                ci_id = data.get('catalog_item_id')
                if ci_id is not None:
                    catalog_item_ids.add(int(ci_id))
            elif provider == 'custom':
                ci_id = data.get('catalog_item_id')
                if ci_id is not None:
                    catalog_item_ids.add(int(ci_id))

        films_by_kp: dict[int, Film] = {}
        if kp_ids:
            film_rows = (
                (await self._session.execute(select(Film).where(Film.kinopoisk_id.in_(kp_ids))))
                .scalars()
                .all()
            )
            for film in film_rows:
                films_by_kp[int(film.kinopoisk_id)] = film

        catalog_by_id: dict[int, CatalogItem] = {}
        catalog_by_external: dict[str, CatalogItem] = {}
        games_by_id: dict[int, Game] = {}
        if catalog_item_ids or rawg_external_ids:
            cq_parts = []
            if catalog_item_ids:
                cq_parts.append(CatalogItem.id.in_(catalog_item_ids))
            if rawg_external_ids:
                cq_parts.append(
                    and_(
                        CatalogItem.provider == CatalogProvider.rawg,
                        CatalogItem.external_id.in_(rawg_external_ids),
                    )
                )
            catalog_rows = (
                (await self._session.execute(select(CatalogItem).where(or_(*cq_parts))))
                .scalars()
                .all()
            )
            game_ids: set[int] = set()
            for ci in catalog_rows:
                catalog_by_id[int(ci.id)] = ci
                catalog_by_external[f'{ci.provider.value}:{ci.external_id}'] = ci
                if ci.game_id is not None:
                    game_ids.add(int(ci.game_id))
            if game_ids:
                game_rows = (
                    (await self._session.execute(select(Game).where(Game.id.in_(game_ids))))
                    .scalars()
                    .all()
                )
                for game in game_rows:
                    games_by_id[int(game.id)] = game

        items: list[WatchlistEntryListItem] = []
        for entry in slice_rows:
            items.append(
                self._hydrate_entry(
                    entry, films_by_kp, catalog_by_id, catalog_by_external, games_by_id
                )
            )

        next_cursor: str | None = None
        if has_more and slice_rows:
            last = slice_rows[-1]
            next_cursor = _encode_cursor(last.created_at, int(last.id))

        return WatchlistEntryPage(items=items, next_cursor=next_cursor)

    async def execute_for_entry(
        self,
        user_id: UUID,
        entry_id: int,
    ) -> WatchlistEntryListItem | None:
        entry = (
            await self._session.execute(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == user_id,
                    WatchlistEntry.id == entry_id,
                )
            )
        ).scalar_one_or_none()
        if entry is None:
            return None
        page = await self.execute(user_id, cursor=None, limit=500)
        for item in page.items:
            if item.entry_id == entry_id:
                return item
        kp_ids: set[int] = set()
        rawg_external_ids: set[str] = set()
        catalog_item_ids: set[int] = set()
        provider = _provider_from_entry(entry)
        data = (entry.provider_meta or {}).get('data') or {}
        if provider == CatalogProvider.kinopoisk.value:
            kp_raw = data.get('kp_id')
            if kp_raw is not None:
                kp_ids.add(int(kp_raw))
            elif entry.card_id.startswith('kp:'):
                kp_ids.add(int(entry.card_id.removeprefix('kp:')))
        elif provider == CatalogProvider.rawg.value:
            slug = data.get('slug') or data.get('external_id')
            if isinstance(slug, str) and slug.strip() != '':
                rawg_external_ids.add(slug.strip())
            elif entry.card_id.startswith('rawg:'):
                rawg_external_ids.add(entry.card_id.removeprefix('rawg:'))
            ci_id = data.get('catalog_item_id')
            if ci_id is not None:
                catalog_item_ids.add(int(ci_id))
        films_by_kp: dict[int, Film] = {}
        if kp_ids:
            film_rows = (
                await self._session.execute(select(Film).where(Film.kinopoisk_id.in_(kp_ids)))
            ).scalars().all()
            for film in film_rows:
                films_by_kp[int(film.kinopoisk_id)] = film
        catalog_by_id: dict[int, CatalogItem] = {}
        catalog_by_external: dict[str, CatalogItem] = {}
        games_by_id: dict[int, Game] = {}
        if catalog_item_ids or rawg_external_ids:
            cq_parts = []
            if catalog_item_ids:
                cq_parts.append(CatalogItem.id.in_(catalog_item_ids))
            if rawg_external_ids:
                cq_parts.append(
                    and_(
                        CatalogItem.provider == CatalogProvider.rawg,
                        CatalogItem.external_id.in_(rawg_external_ids),
                    )
                )
            catalog_rows = (
                await self._session.execute(select(CatalogItem).where(or_(*cq_parts)))
            ).scalars().all()
            game_ids: set[int] = set()
            for ci in catalog_rows:
                catalog_by_id[int(ci.id)] = ci
                catalog_by_external[f'{ci.provider.value}:{ci.external_id}'] = ci
                if ci.game_id is not None:
                    game_ids.add(int(ci.game_id))
            if game_ids:
                game_rows = (
                    await self._session.execute(select(Game).where(Game.id.in_(game_ids)))
                ).scalars().all()
                for game in game_rows:
                    games_by_id[int(game.id)] = game
        return self._hydrate_entry(entry, films_by_kp, catalog_by_id, catalog_by_external, games_by_id)

    def _hydrate_entry(
        self,
        entry: WatchlistEntry,
        films_by_kp: dict[int, Film],
        catalog_by_id: dict[int, CatalogItem],
        catalog_by_external: dict[str, CatalogItem],
        games_by_id: dict[int, Game],
    ) -> WatchlistEntryListItem:
        provider = _provider_from_entry(entry)
        data = (entry.provider_meta or {}).get('data') or {}
        title = 'Untitled'
        poster_url: str | None = None
        year: int | None = None
        film_id: int | None = None
        film_kinopoisk_id: int | None = None
        film_genres: list[str] | None = None
        catalog_item_id: int | None = None
        external_id: str | None = None

        if provider == CatalogProvider.kinopoisk.value:
            kp_raw = data.get('kp_id')
            kp_id = int(kp_raw) if kp_raw is not None else int(entry.card_id.removeprefix('kp:'))
            film = films_by_kp.get(kp_id)
            if film is not None:
                title = film.title
                poster_url = film.poster_url
                year = film.year
                film_id = int(film.id)
                film_kinopoisk_id = int(film.kinopoisk_id)
                film_genres = list(film.genres or [])
            else:
                title = str(data.get('title') or f'Kinopoisk #{kp_id}')
                film_kinopoisk_id = kp_id
            external_id = str(kp_id)
        elif provider == CatalogProvider.rawg.value:
            slug = data.get('slug') or data.get('external_id')
            if not isinstance(slug, str) or slug.strip() == '':
                slug = (
                    entry.card_id.removeprefix('rawg:')
                    if entry.card_id.startswith('rawg:')
                    else None
                )
            external_id = str(slug) if slug is not None else None
            ci: CatalogItem | None = None
            ci_id_raw = data.get('catalog_item_id')
            if ci_id_raw is not None:
                catalog_item_id = int(ci_id_raw)
                ci = catalog_by_id.get(catalog_item_id)
            if ci is None and external_id is not None:
                ci = catalog_by_external.get(f'{CatalogProvider.rawg.value}:{external_id}')
            if ci is not None:
                catalog_item_id = int(ci.id)
                if ci.film_id is not None:
                    film_id = int(ci.film_id)
                if ci.game_id is not None:
                    game = games_by_id.get(int(ci.game_id))
                    if game is not None:
                        title = str(game.name or data.get('title') or external_id or 'Game')
                        poster_url = game.background_image
                        year = _year_from_released(game.released)
            if title == 'Untitled':
                title = str(data.get('title') or external_id or entry.card_id)
                poster_url = data.get('poster_url') or data.get('display_cover_url')
        else:
            title = str(
                data.get('title')
                or data.get('display_title')
                or entry.card_id.removeprefix('custom:')
            )
            poster_url = data.get('poster_url') or data.get('display_cover_url')
            year_raw = data.get('year')
            if year_raw is not None:
                try:
                    year = int(year_raw)
                except (TypeError, ValueError):
                    year = None

        return WatchlistEntryListItem(
            entry_id=int(entry.id),
            card_id=entry.card_id,
            provider=provider,
            title=title,
            poster_url=poster_url,
            year=year,
            watch_tag=entry.watch_tag,
            watch_with_user_id=entry.watch_with_user_id,
            created_at=entry.created_at,
            film_id=film_id,
            film_kinopoisk_id=film_kinopoisk_id,
            film_genres=film_genres,
            catalog_item_id=catalog_item_id,
            external_id=external_id,
        )
