from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
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
    watch_with_user_ids: list[UUID]
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


@dataclass(frozen=True, slots=True)
class _HydrationKeys:
    kp_ids: set[int] = field(default_factory=set)
    rawg_external_ids: set[str] = field(default_factory=set)
    catalog_item_ids: set[int] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class _HydrationMaps:
    films_by_kp: dict[int, Film]
    catalog_by_id: dict[int, CatalogItem]
    catalog_by_external: dict[str, CatalogItem]
    games_by_id: dict[int, Game]


def _collect_hydration_keys(entries: list[WatchlistEntry]) -> _HydrationKeys:
    kp_ids: set[int] = set()
    rawg_external_ids: set[str] = set()
    catalog_item_ids: set[int] = set()

    for entry in entries:
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

    return _HydrationKeys(
        kp_ids=kp_ids,
        rawg_external_ids=rawg_external_ids,
        catalog_item_ids=catalog_item_ids,
    )


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
        cursor_ts, cursor_id = self._parse_cursor(cursor)
        cap = max(1, min(limit, 50))
        slice_rows = await self._fetch_entries(user_id, cursor_ts, cursor_id, cap)
        if not slice_rows:
            return WatchlistEntryPage(items=[], next_cursor=None)

        has_more = len(slice_rows) > cap
        page_rows = slice_rows[:cap] if has_more else slice_rows
        maps = await self._load_hydration_maps(_collect_hydration_keys(page_rows))
        items = [self._hydrate_entry(entry, maps) for entry in page_rows]

        next_cursor: str | None = None
        if has_more:
            last = page_rows[-1]
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
        maps = await self._load_hydration_maps(_collect_hydration_keys([entry]))
        return self._hydrate_entry(entry, maps)

    def _parse_cursor(self, cursor: str | None) -> tuple[dt.datetime | None, int | None]:
        if cursor is None or cursor.strip() == '':
            return None, None
        decoded = _decode_cursor(cursor.strip())
        if decoded is None:
            raise self.InvalidCursor
        return decoded

    async def _fetch_entries(
        self,
        user_id: UUID,
        cursor_ts: dt.datetime | None,
        cursor_id: int | None,
        cap: int,
    ) -> list[WatchlistEntry]:
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
        return list((await self._session.execute(stmt)).scalars().all())

    async def _load_hydration_maps(self, keys: _HydrationKeys) -> _HydrationMaps:
        films_by_kp: dict[int, Film] = {}
        if keys.kp_ids:
            film_rows = (
                (
                    await self._session.execute(
                        select(Film).where(Film.kinopoisk_id.in_(keys.kp_ids))
                    )
                )
                .scalars()
                .all()
            )
            for film in film_rows:
                films_by_kp[int(film.kinopoisk_id)] = film

        catalog_by_id: dict[int, CatalogItem] = {}
        catalog_by_external: dict[str, CatalogItem] = {}
        games_by_id: dict[int, Game] = {}
        if keys.catalog_item_ids or keys.rawg_external_ids:
            cq_parts = []
            if keys.catalog_item_ids:
                cq_parts.append(CatalogItem.id.in_(keys.catalog_item_ids))
            if keys.rawg_external_ids:
                cq_parts.append(
                    and_(
                        CatalogItem.provider == CatalogProvider.rawg,
                        CatalogItem.external_id.in_(keys.rawg_external_ids),
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

        return _HydrationMaps(
            films_by_kp=films_by_kp,
            catalog_by_id=catalog_by_id,
            catalog_by_external=catalog_by_external,
            games_by_id=games_by_id,
        )

    def _hydrate_entry(self, entry: WatchlistEntry, maps: _HydrationMaps) -> WatchlistEntryListItem:
        provider = _provider_from_entry(entry)
        if provider == CatalogProvider.kinopoisk.value:
            fields = self._hydrate_kinopoisk(entry, maps.films_by_kp)
        elif provider == CatalogProvider.rawg.value:
            fields = self._hydrate_rawg(entry, maps)
        else:
            fields = self._hydrate_custom(entry)

        return WatchlistEntryListItem(
            entry_id=int(entry.id),
            card_id=entry.card_id,
            provider=provider,
            watch_tag=entry.watch_tag,
            watch_with_user_id=entry.watch_with_user_id,
            watch_with_user_ids=[UUID(str(raw)) for raw in (entry.watch_with_user_ids or [])],
            created_at=entry.created_at,
            **fields,
        )

    def _hydrate_kinopoisk(
        self,
        entry: WatchlistEntry,
        films_by_kp: dict[int, Film],
    ) -> dict[str, object]:
        data = (entry.provider_meta or {}).get('data') or {}
        kp_raw = data.get('kp_id')
        kp_id = int(kp_raw) if kp_raw is not None else int(entry.card_id.removeprefix('kp:'))
        film = films_by_kp.get(kp_id)
        if film is not None:
            return {
                'title': film.title,
                'poster_url': film.poster_url,
                'year': film.year,
                'film_id': int(film.id),
                'film_kinopoisk_id': int(film.kinopoisk_id),
                'film_genres': list(film.genres or []),
                'catalog_item_id': None,
                'external_id': str(kp_id),
            }
        return {
            'title': str(data.get('title') or f'Kinopoisk #{kp_id}'),
            'poster_url': None,
            'year': None,
            'film_id': None,
            'film_kinopoisk_id': kp_id,
            'film_genres': None,
            'catalog_item_id': None,
            'external_id': str(kp_id),
        }

    def _hydrate_rawg(self, entry: WatchlistEntry, maps: _HydrationMaps) -> dict[str, object]:
        data = (entry.provider_meta or {}).get('data') or {}
        slug = data.get('slug') or data.get('external_id')
        if not isinstance(slug, str) or slug.strip() == '':
            slug = (
                entry.card_id.removeprefix('rawg:') if entry.card_id.startswith('rawg:') else None
            )
        external_id = str(slug) if slug is not None else None

        catalog_item_id: int | None = None
        film_id: int | None = None
        title = 'Untitled'
        poster_url: str | None = None
        year: int | None = None

        ci: CatalogItem | None = None
        ci_id_raw = data.get('catalog_item_id')
        if ci_id_raw is not None:
            catalog_item_id = int(ci_id_raw)
            ci = maps.catalog_by_id.get(catalog_item_id)
        if ci is None and external_id is not None:
            ci = maps.catalog_by_external.get(f'{CatalogProvider.rawg.value}:{external_id}')
        if ci is not None:
            catalog_item_id = int(ci.id)
            if ci.film_id is not None:
                film_id = int(ci.film_id)
            if ci.game_id is not None:
                game = maps.games_by_id.get(int(ci.game_id))
                if game is not None:
                    title = str(game.name or data.get('title') or external_id or 'Game')
                    poster_url = game.background_image
                    year = _year_from_released(game.released)
        if title == 'Untitled':
            title = str(data.get('title') or external_id or entry.card_id)
            poster_url = data.get('poster_url') or data.get('display_cover_url')

        return {
            'title': title,
            'poster_url': poster_url,
            'year': year,
            'film_id': film_id,
            'film_kinopoisk_id': None,
            'film_genres': None,
            'catalog_item_id': catalog_item_id,
            'external_id': external_id,
        }

    def _hydrate_custom(self, entry: WatchlistEntry) -> dict[str, object]:
        data = (entry.provider_meta or {}).get('data') or {}
        year: int | None = None
        year_raw = data.get('year')
        if year_raw is not None:
            try:
                year = int(year_raw)
            except (TypeError, ValueError):
                year = None
        return {
            'title': str(
                data.get('title')
                or data.get('display_title')
                or entry.card_id.removeprefix('custom:')
            ),
            'poster_url': data.get('poster_url') or data.get('display_cover_url'),
            'year': year,
            'film_id': None,
            'film_kinopoisk_id': None,
            'film_genres': None,
            'catalog_item_id': None,
            'external_id': None,
        }
