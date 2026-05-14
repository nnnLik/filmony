"""DTO и query-параметры строго по ``openapi-rawg.json`` (definitions ``Game``, ``GameSingle``)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Self

from utils.http_url import normalize_absolute_http_url


class RawgGameDtoParseError(Exception):
    """JSON ответа RAWG не соответствует ожидаемой схеме OpenAPI."""


def _require_int(d: dict[str, Any], key: str) -> int:
    if key not in d:
        raise RawgGameDtoParseError(f'missing required field {key}')
    v = d[key]
    if isinstance(v, bool) or not isinstance(v, int):
        raise RawgGameDtoParseError(f'invalid int for {key}')
    return v


def _optional_int(d: dict[str, Any], key: str) -> int | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if isinstance(v, bool) or not isinstance(v, int):
        return None
    return v


def _require_number(d: dict[str, Any], key: str) -> float:
    if key not in d:
        raise RawgGameDtoParseError(f'missing required field {key}')
    v = d[key]
    if isinstance(v, bool):
        raise RawgGameDtoParseError(f'invalid number for {key}')
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    raise RawgGameDtoParseError(f'invalid number for {key}')


def _optional_str(d: dict[str, Any], key: str) -> str | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if not isinstance(v, str):
        return None
    text = v.strip()
    return text if text else None


def _optional_bool(d: dict[str, Any], key: str) -> bool | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if not isinstance(v, bool):
        return None
    return v


def _optional_uri(d: dict[str, Any], key: str) -> str | None:
    s = _optional_str(d, key)
    if s is None:
        return None
    return normalize_absolute_http_url(s)


type RawgOpenObjectOrArray = Mapping[str, Any] | tuple[Any, ...]


def _open_object_or_array(d: dict[str, Any], key: str) -> RawgOpenObjectOrArray:
    """OpenAPI ``object``, но в живом API часто массив (напр. ``ratings`` — список агрегатов по звёздам)."""

    raw = d.get(key)
    if raw is None:
        return MappingProxyType({})
    if isinstance(raw, dict):
        return MappingProxyType(dict(raw))
    if isinstance(raw, list):
        return tuple(raw)
    raise RawgGameDtoParseError(f'field {key} must be an object or array')


def rawg_open_blob_to_plain_json(blob: RawgOpenObjectOrArray) -> dict[str, Any] | list[Any]:
    """Снимок/JSON‑колонки: вернуть обычный ``dict`` или ``list`` (элементы не копируем глубоко)."""

    if isinstance(blob, Mapping):
        return dict(blob)
    return list(blob)


@dataclass(frozen=True, slots=True)
class RawgEsrbRatingDTO:
    """Вложенный объект ``esrb_rating`` (см. ``Game`` / ``GameSingle``)."""

    id: int | None
    slug: str | None
    name: str | None

    @classmethod
    def from_optional_dict(cls, raw: Any) -> RawgEsrbRatingDTO | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            return None
        return cls(
            id=_optional_int(raw, 'id'),
            slug=_optional_str(raw, 'slug'),
            name=_optional_str(raw, 'name'),
        )


@dataclass(frozen=True, slots=True)
class RawgGamePlatformRefDTO:
    """``platform`` внутри элемента ``platforms[]``."""

    id: int | None
    slug: str | None
    name: str | None

    @classmethod
    def from_optional_dict(cls, raw: Any) -> RawgGamePlatformRefDTO | None:
        if raw is None or not isinstance(raw, dict):
            return None
        return cls(
            id=_optional_int(raw, 'id'),
            slug=_optional_str(raw, 'slug'),
            name=_optional_str(raw, 'name'),
        )


@dataclass(frozen=True, slots=True)
class RawgGamePlatformRequirementsDTO:
    """``requirements`` в элементе ``platforms[]``."""

    minimum: str | None
    recommended: str | None

    @classmethod
    def from_optional_dict(cls, raw: Any) -> RawgGamePlatformRequirementsDTO | None:
        if raw is None or not isinstance(raw, dict):
            return None
        return cls(
            minimum=_optional_str(raw, 'minimum'),
            recommended=_optional_str(raw, 'recommended'),
        )


@dataclass(frozen=True, slots=True)
class RawgGamePlatformItemDTO:
    """Элемент массива ``platforms`` (``Game`` / ``GameSingle``)."""

    platform: RawgGamePlatformRefDTO | None
    released_at: str | None
    requirements: RawgGamePlatformRequirementsDTO | None

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> Self:
        return cls(
            platform=RawgGamePlatformRefDTO.from_optional_dict(row.get('platform')),
            released_at=_optional_str(row, 'released_at'),
            requirements=RawgGamePlatformRequirementsDTO.from_optional_dict(row.get('requirements')),
        )


@dataclass(frozen=True, slots=True)
class RawgGamePlatformMetacriticDTO:
    """``#/definitions/GamePlatformMetacritic``."""

    metascore: int | None
    url: str | None

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> Self:
        return cls(
            metascore=_optional_int(row, 'metascore'),
            url=_optional_str(row, 'url'),
        )


def _platform_items_tuple(raw: Any) -> tuple[RawgGamePlatformItemDTO, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[RawgGamePlatformItemDTO] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(RawgGamePlatformItemDTO.from_dict(item))
    return tuple(out)


def _metacritic_platforms_tuple(raw: Any) -> tuple[RawgGamePlatformMetacriticDTO, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[RawgGamePlatformMetacriticDTO] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(RawgGamePlatformMetacriticDTO.from_dict(item))
    return tuple(out)


def _alternative_names_tuple(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    names: list[str] = []
    for item in raw:
        if isinstance(item, str):
            t = item.strip()
            if t:
                names.append(t)
    return tuple(names)


@dataclass(frozen=True, slots=True)
class RawgGameDTO:
    """``#/definitions/Game`` — элемент ``results[]`` для ``GET /games``."""

    id: int | None
    slug: str | None
    name: str | None
    released: str | None
    tba: bool | None
    background_image: str | None
    rating: float
    rating_top: int | None
    ratings: RawgOpenObjectOrArray
    ratings_count: int | None
    reviews_text_count: str | None
    added: int | None
    added_by_status: RawgOpenObjectOrArray
    metacritic: int | None
    playtime: int | None
    suggestions_count: int | None
    updated: str | None
    esrb_rating: RawgEsrbRatingDTO | None
    platforms: tuple[RawgGamePlatformItemDTO, ...]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            id=_optional_int(d, 'id'),
            slug=_optional_str(d, 'slug'),
            name=_optional_str(d, 'name'),
            released=_optional_str(d, 'released'),
            tba=_optional_bool(d, 'tba'),
            background_image=_optional_uri(d, 'background_image'),
            rating=_require_number(d, 'rating'),
            rating_top=_optional_int(d, 'rating_top'),
            ratings=_open_object_or_array(d, 'ratings'),
            ratings_count=_optional_int(d, 'ratings_count'),
            reviews_text_count=_optional_str(d, 'reviews_text_count'),
            added=_optional_int(d, 'added'),
            added_by_status=_open_object_or_array(d, 'added_by_status'),
            metacritic=_optional_int(d, 'metacritic'),
            playtime=_optional_int(d, 'playtime'),
            suggestions_count=_optional_int(d, 'suggestions_count'),
            updated=_optional_str(d, 'updated'),
            esrb_rating=RawgEsrbRatingDTO.from_optional_dict(d.get('esrb_rating')),
            platforms=_platform_items_tuple(d.get('platforms')),
        )


@dataclass(frozen=True, slots=True)
class RawgGameSingleDTO:
    """``#/definitions/GameSingle`` — тело ``GET /games/{id}``."""

    id: int | None
    slug: str | None
    name: str | None
    name_original: str | None
    description: str | None
    metacritic: int | None
    metacritic_platforms: tuple[RawgGamePlatformMetacriticDTO, ...]
    released: str | None
    tba: bool | None
    updated: str | None
    background_image: str | None
    background_image_additional: str | None
    website: str | None
    rating: float
    rating_top: int | None
    ratings: RawgOpenObjectOrArray
    reactions: RawgOpenObjectOrArray
    added: int | None
    added_by_status: RawgOpenObjectOrArray
    playtime: int | None
    screenshots_count: int | None
    movies_count: int | None
    creators_count: int | None
    achievements_count: int | None
    parent_achievements_count: str | None
    reddit_url: str | None
    reddit_name: str | None
    reddit_description: str | None
    reddit_logo: str | None
    reddit_count: int | None
    twitch_count: str | None
    youtube_count: str | None
    reviews_text_count: str | None
    ratings_count: int | None
    suggestions_count: int | None
    alternative_names: tuple[str, ...]
    metacritic_url: str | None
    parents_count: int | None
    additions_count: int | None
    game_series_count: int | None
    esrb_rating: RawgEsrbRatingDTO | None
    platforms: tuple[RawgGamePlatformItemDTO, ...]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            id=_optional_int(d, 'id'),
            slug=_optional_str(d, 'slug'),
            name=_optional_str(d, 'name'),
            name_original=_optional_str(d, 'name_original'),
            description=_optional_str(d, 'description'),
            metacritic=_optional_int(d, 'metacritic'),
            metacritic_platforms=_metacritic_platforms_tuple(d.get('metacritic_platforms')),
            released=_optional_str(d, 'released'),
            tba=_optional_bool(d, 'tba'),
            updated=_optional_str(d, 'updated'),
            background_image=_optional_uri(d, 'background_image'),
            background_image_additional=_optional_str(d, 'background_image_additional'),
            website=_optional_uri(d, 'website'),
            rating=_require_number(d, 'rating'),
            rating_top=_optional_int(d, 'rating_top'),
            ratings=_open_object_or_array(d, 'ratings'),
            reactions=_open_object_or_array(d, 'reactions'),
            added=_optional_int(d, 'added'),
            added_by_status=_open_object_or_array(d, 'added_by_status'),
            playtime=_optional_int(d, 'playtime'),
            screenshots_count=_optional_int(d, 'screenshots_count'),
            movies_count=_optional_int(d, 'movies_count'),
            creators_count=_optional_int(d, 'creators_count'),
            achievements_count=_optional_int(d, 'achievements_count'),
            parent_achievements_count=_optional_str(d, 'parent_achievements_count'),
            reddit_url=_optional_str(d, 'reddit_url'),
            reddit_name=_optional_str(d, 'reddit_name'),
            reddit_description=_optional_str(d, 'reddit_description'),
            reddit_logo=_optional_uri(d, 'reddit_logo'),
            reddit_count=_optional_int(d, 'reddit_count'),
            twitch_count=_optional_str(d, 'twitch_count'),
            youtube_count=_optional_str(d, 'youtube_count'),
            reviews_text_count=_optional_str(d, 'reviews_text_count'),
            ratings_count=_optional_int(d, 'ratings_count'),
            suggestions_count=_optional_int(d, 'suggestions_count'),
            alternative_names=_alternative_names_tuple(d.get('alternative_names')),
            metacritic_url=_optional_str(d, 'metacritic_url'),
            parents_count=_optional_int(d, 'parents_count'),
            additions_count=_optional_int(d, 'additions_count'),
            game_series_count=_optional_int(d, 'game_series_count'),
            esrb_rating=RawgEsrbRatingDTO.from_optional_dict(d.get('esrb_rating')),
            platforms=_platform_items_tuple(d.get('platforms')),
        )


@dataclass(frozen=True, slots=True)
class RawgGamesListResponseDTO:
    """Тело ответа 200 ``GET /games`` (``count``, ``next``, ``previous``, ``results``)."""

    count: int
    next_url: str | None
    previous_url: str | None
    results: tuple[RawgGameDTO, ...]

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> Self:
        count = _require_int(doc, 'count')
        if count < 0:
            raise RawgGameDtoParseError('count must be non-negative')
        results_raw = doc.get('results')
        if not isinstance(results_raw, list):
            raise RawgGameDtoParseError('results must be a list')
        games: list[RawgGameDTO] = []
        for row in results_raw:
            if not isinstance(row, dict):
                raise RawgGameDtoParseError('each results item must be an object')
            games.append(RawgGameDTO.from_dict(row))
        return cls(
            count=count,
            next_url=_optional_str(doc, 'next'),
            previous_url=_optional_str(doc, 'previous'),
            results=tuple(games),
        )


@dataclass(frozen=True, slots=True)
class RawgGamesListQueryParams:
    """Все query-параметры ``GET /games`` из OpenAPI (все опциональны кроме отсутствия в спеке — передаём только не-``None``)."""

    search: str | None = None
    page: int | None = None
    page_size: int | None = None
    search_precise: bool | None = None
    search_exact: bool | None = None
    parent_platforms: str | None = None
    platforms: str | None = None
    stores: str | None = None
    developers: str | None = None
    publishers: str | None = None
    genres: str | None = None
    tags: str | None = None
    creators: str | None = None
    dates: str | None = None
    updated: str | None = None
    platforms_count: int | None = None
    metacritic: str | None = None
    exclude_collection: int | None = None
    exclude_additions: bool | None = None
    exclude_parents: bool | None = None
    exclude_game_series: bool | None = None
    exclude_stores: str | None = None
    ordering: str | None = None

    def to_params(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.search is not None:
            out['search'] = self.search
        if self.page is not None:
            out['page'] = self.page
        if self.page_size is not None:
            out['page_size'] = self.page_size
        if self.search_precise is not None:
            out['search_precise'] = self.search_precise
        if self.search_exact is not None:
            out['search_exact'] = self.search_exact
        if self.parent_platforms is not None:
            out['parent_platforms'] = self.parent_platforms
        if self.platforms is not None:
            out['platforms'] = self.platforms
        if self.stores is not None:
            out['stores'] = self.stores
        if self.developers is not None:
            out['developers'] = self.developers
        if self.publishers is not None:
            out['publishers'] = self.publishers
        if self.genres is not None:
            out['genres'] = self.genres
        if self.tags is not None:
            out['tags'] = self.tags
        if self.creators is not None:
            out['creators'] = self.creators
        if self.dates is not None:
            out['dates'] = self.dates
        if self.updated is not None:
            out['updated'] = self.updated
        if self.platforms_count is not None:
            out['platforms_count'] = self.platforms_count
        if self.metacritic is not None:
            out['metacritic'] = self.metacritic
        if self.exclude_collection is not None:
            out['exclude_collection'] = self.exclude_collection
        if self.exclude_additions is not None:
            out['exclude_additions'] = self.exclude_additions
        if self.exclude_parents is not None:
            out['exclude_parents'] = self.exclude_parents
        if self.exclude_game_series is not None:
            out['exclude_game_series'] = self.exclude_game_series
        if self.exclude_stores is not None:
            out['exclude_stores'] = self.exclude_stores
        if self.ordering is not None:
            out['ordering'] = self.ordering
        return out

    @classmethod
    def for_search(
        cls,
        *,
        search: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Self:
        return cls(search=search, page=page, page_size=page_size)
