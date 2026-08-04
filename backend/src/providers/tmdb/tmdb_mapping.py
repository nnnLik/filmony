from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from providers.tmdb.tmdb_credits_dto import TmdbCreditsDTO, TmdbCrewMemberDTO
from providers.tmdb.tmdb_movie_dto import TmdbCollectionRefDTO, TmdbMovieDetailDTO


def normalize_imdb_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = raw.strip()
    if text == '':
        return None
    if text.startswith('tt'):
        return text
    if re.fullmatch(r'\d+', text):
        return f'tt{text}'
    return text


def countries_from_movie(dto: TmdbMovieDetailDTO) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for country in dto.production_countries:
        name = country.name.strip()
        if name == '':
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(name)
    return ordered


def first_director_from_credits(credits: TmdbCreditsDTO) -> TmdbCrewMemberDTO | None:
    for member in credits.crew:
        if member.job == 'Director':
            return member
    return None


def franchise_key_from_movie(
    *,
    kinopoisk_id: int,
    collection: TmdbCollectionRefDTO | None,
) -> str:
    if collection is not None:
        return f'tmdb_collection:{collection.id}'
    return f'kp_franchise:{kinopoisk_id}'


def collection_name_from_snapshot(snapshot: dict[str, Any] | None) -> str | None:
    if not isinstance(snapshot, dict):
        return None
    collection = snapshot.get('belongs_to_collection')
    if not isinstance(collection, dict):
        return None
    name = collection.get('name')
    if not isinstance(name, str):
        return None
    text = name.strip()
    return text if text else None


@dataclass(frozen=True, slots=True)
class TmdbGamificationPreview:
    countries: list[str]
    primary_director_tmdb_id: int | None
    primary_director_name: str | None
    franchise_key: str


def gamification_preview_from_movie(
    dto: TmdbMovieDetailDTO,
    *,
    kinopoisk_id: int,
) -> TmdbGamificationPreview:
    director = first_director_from_credits(dto.credits) if dto.credits is not None else None
    return TmdbGamificationPreview(
        countries=countries_from_movie(dto),
        primary_director_tmdb_id=director.id if director is not None else None,
        primary_director_name=director.name if director is not None else None,
        franchise_key=franchise_key_from_movie(
            kinopoisk_id=kinopoisk_id,
            collection=dto.belongs_to_collection,
        ),
    )


__all__ = (
    'TmdbGamificationPreview',
    'collection_name_from_snapshot',
    'countries_from_movie',
    'first_director_from_credits',
    'franchise_key_from_movie',
    'gamification_preview_from_movie',
    'normalize_imdb_id',
)
