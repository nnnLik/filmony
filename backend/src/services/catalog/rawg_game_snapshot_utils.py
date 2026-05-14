"""JSON snapshots and merging rules for persisted ``Game`` rows from RAWG DTOs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from models.game import Game
from providers.rawg.rawg_openapi_dto import (
    RawgEsrbRatingDTO,
    RawgGameDTO,
    RawgGamePlatformItemDTO,
    RawgGamePlatformMetacriticDTO,
    RawgGameSingleDTO,
)


def utc_now() -> datetime:
    """Naive UTC for columns mapped as TIMESTAMP WITHOUT TIME ZONE."""

    return datetime.now(tz=UTC).replace(tzinfo=None)


def _serialize_esrb(e: RawgEsrbRatingDTO | None) -> dict[str, Any] | None:
    if e is None:
        return None
    return {'id': e.id, 'slug': e.slug, 'name': e.name}


def serialize_platform_items(items: tuple[RawgGamePlatformItemDTO, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in items:
        row: dict[str, Any] = {'released_at': p.released_at, 'requirements': None, 'platform': None}
        req = p.requirements
        if req is not None:
            row['requirements'] = {'minimum': req.minimum, 'recommended': req.recommended}
        plat = p.platform
        if plat is not None:
            row['platform'] = {'id': plat.id, 'slug': plat.slug, 'name': plat.name}
        rows.append(row)
    return rows


def rawg_game_dto_list_snapshot(dto: RawgGameDTO) -> dict[str, Any]:
    """JSON snapshot compatible with RAWG ``Game`` definition (list/search)."""

    ratings = dict[str, Any](dto.ratings)
    added_by_status = dict[str, Any](dto.added_by_status)
    return {
        'id': dto.id,
        'slug': dto.slug,
        'name': dto.name,
        'released': dto.released,
        'tba': dto.tba,
        'background_image': dto.background_image,
        'rating': dto.rating,
        'rating_top': dto.rating_top,
        'ratings': ratings,
        'ratings_count': dto.ratings_count,
        'reviews_text_count': dto.reviews_text_count,
        'added': dto.added,
        'added_by_status': added_by_status,
        'metacritic': dto.metacritic,
        'playtime': dto.playtime,
        'suggestions_count': dto.suggestions_count,
        'updated': dto.updated,
        'esrb_rating': _serialize_esrb(dto.esrb_rating),
        'platforms': serialize_platform_items(dto.platforms),
    }


def rawg_game_single_snapshot(dto: RawgGameSingleDTO) -> dict[str, Any]:
    """Rich JSON snapshot for RAWG ``GameSingle``."""

    reactions = dict[str, Any](dto.reactions)
    ratings = dict[str, Any](dto.ratings)
    added_by_status = dict[str, Any](dto.added_by_status)
    mplat: list[dict[str, Any]] = [
        {'metascore': m.metascore, 'url': m.url} for m in dto.metacritic_platforms
    ]
    return {
        'id': dto.id,
        'slug': dto.slug,
        'name': dto.name,
        'name_original': dto.name_original,
        'description': dto.description,
        'metacritic': dto.metacritic,
        'metacritic_platforms': mplat,
        'released': dto.released,
        'tba': dto.tba,
        'updated': dto.updated,
        'background_image': dto.background_image,
        'background_image_additional': dto.background_image_additional,
        'website': dto.website,
        'rating': dto.rating,
        'rating_top': dto.rating_top,
        'ratings': ratings,
        'reactions': reactions,
        'added': dto.added,
        'added_by_status': added_by_status,
        'playtime': dto.playtime,
        'screenshots_count': dto.screenshots_count,
        'movies_count': dto.movies_count,
        'creators_count': dto.creators_count,
        'achievements_count': dto.achievements_count,
        'reviews_text_count': dto.reviews_text_count,
        'ratings_count': dto.ratings_count,
        'suggestions_count': dto.suggestions_count,
        'alternative_names': list(dto.alternative_names),
        'parents_count': dto.parents_count,
        'additions_count': dto.additions_count,
        'game_series_count': dto.game_series_count,
        'esrb_rating': _serialize_esrb(dto.esrb_rating),
        'platforms': serialize_platform_items(dto.platforms),
    }


def merge_list_dto_into_game(game: Game, dto: RawgGameDTO, *, synced_at: datetime) -> None:
    """Updates list-available columns; skips None DTO fields to avoid wiping prior detail."""

    assert dto.id is not None
    game.rawg_id = dto.id
    if dto.slug is not None:
        game.slug = dto.slug
    if dto.name is not None:
        game.name = dto.name
    if dto.released is not None:
        game.released = dto.released
    if dto.tba is not None:
        game.tba = dto.tba
    if dto.background_image is not None:
        game.background_image = dto.background_image

    game.rating = dto.rating
    if dto.rating_top is not None:
        game.rating_top = dto.rating_top
    if dto.ratings_count is not None:
        game.ratings_count = dto.ratings_count
    if dto.metacritic is not None:
        game.metacritic = dto.metacritic

    game.ratings_json = dict[str, Any](dto.ratings)
    game.added_by_status_json = dict[str, Any](dto.added_by_status)

    plat = serialize_platform_items(dto.platforms)
    if plat:
        game.platforms_json = plat

    esrb_doc = _serialize_esrb(dto.esrb_rating)
    if esrb_doc is not None:
        game.esrb_rating_json = esrb_doc

    game.raw_search_snapshot = rawg_game_dto_list_snapshot(dto)
    game.search_synced_at = synced_at


def _assign_if_text(game: Game, attr: str, value: str | None) -> None:
    if value is None:
        return
    setattr(game, attr, value)


def _assign_if_optional_int(game: Game, attr: str, value: int | None) -> None:
    if value is None:
        return
    setattr(game, attr, value)


def merge_detail_dto_into_game(game: Game, dto: RawgGameSingleDTO, *, synced_at: datetime) -> None:
    """Fills richer detail fields without clearing unspecified values where DTO lacks data."""

    assert dto.id is not None
    game.rawg_id = dto.id
    _assign_if_text(game, 'slug', dto.slug)
    _assign_if_text(game, 'name', dto.name)
    _assign_if_text(game, 'name_original', dto.name_original)
    _assign_if_text(game, 'description', dto.description)
    _assign_if_text(game, 'released', dto.released)
    _assign_if_text(game, 'background_image', dto.background_image)
    _assign_if_text(game, 'background_image_additional', dto.background_image_additional)
    _assign_if_text(game, 'website', dto.website)

    _assign_if_optional_int(game, 'metacritic', dto.metacritic)
    game.rating = dto.rating
    _assign_if_optional_int(game, 'rating_top', dto.rating_top)
    _assign_if_optional_int(game, 'ratings_count', dto.ratings_count)

    if dto.tba is not None:
        game.tba = dto.tba

    game.ratings_json = dict[str, Any](dto.ratings)
    game.reactions_json = dict[str, Any](dto.reactions)
    game.added_by_status_json = dict[str, Any](dto.added_by_status)

    mplat_rows: list[dict[str, Any]] = [
        {'metascore': m.metascore, 'url': m.url} for m in dto.metacritic_platforms
    ]
    if mplat_rows:
        game.metacritic_platforms_json = mplat_rows

    plat = serialize_platform_items(dto.platforms)
    if plat:
        game.platforms_json = plat

    esrb_doc = _serialize_esrb(dto.esrb_rating)
    if esrb_doc is not None:
        game.esrb_rating_json = esrb_doc

    if dto.alternative_names:
        game.alternative_names_json = list(dto.alternative_names)

    game.raw_detail_snapshot = rawg_game_single_snapshot(dto)
    game.detail_synced_at = synced_at

