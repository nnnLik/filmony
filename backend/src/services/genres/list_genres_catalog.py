from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.genre_slug import genre_slug
from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters


@dataclass(frozen=True, slots=True)
class GenreCatalogItemDTO:
    slug: str
    genre: str
    films_count: int


@dataclass(frozen=True, slots=True)
class GenresCatalogPageDTO:
    items: list[GenreCatalogItemDTO]
    next_cursor: str | None


def _encode_genres_cursor(films_count: int, slug: str) -> str:
    return f'{films_count}:{slug}'


def _decode_genres_cursor(cursor: str) -> tuple[int, str] | None:
    parts = cursor.split(':', 1)
    if len(parts) != 2:
        return None
    try:
        films_count = int(parts[0], 10)
    except ValueError:
        return None
    slug = parts[1].strip()
    if films_count < 0 or slug == '':
        return None
    return films_count, slug


@dataclass
class ListGenresCatalogService:
    """Lists distinct genres from rated films with community counts."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, cursor: str | None, limit: int) -> GenresCatalogPageDTO:
        rows = (
            await self._session.execute(
                select(Film.genres)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(*_rated_card_filters())
            )
        ).all()

        slug_to_genre: dict[str, str] = {}
        slug_counts: dict[str, int] = {}
        for (genres,) in rows:
            seen_in_film: set[str] = set()
            for genre in genres or []:
                name = str(genre).strip()
                if name == '':
                    continue
                slug = genre_slug(name)
                if slug in seen_in_film:
                    continue
                seen_in_film.add(slug)
                slug_to_genre.setdefault(slug, name)
                slug_counts[slug] = slug_counts.get(slug, 0) + 1

        sorted_items = sorted(
            slug_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )

        start_idx = 0
        if cursor is not None and cursor != '':
            decoded = _decode_genres_cursor(cursor)
            if decoded is None:
                raise self.InvalidCursor
            cursor_count, cursor_slug = decoded
            for idx, (slug, count) in enumerate(sorted_items):
                if count < cursor_count or (count == cursor_count and slug < cursor_slug):
                    start_idx = idx
                    break
            else:
                start_idx = len(sorted_items)

        visible = sorted_items[start_idx : start_idx + limit + 1]
        has_more = len(visible) > limit
        page_items = visible[:limit]

        items = [
            GenreCatalogItemDTO(
                slug=slug,
                genre=slug_to_genre.get(slug, slug),
                films_count=count,
            )
            for slug, count in page_items
        ]

        next_cursor: str | None = None
        if has_more and page_items:
            last_slug, last_count = page_items[-1]
            next_cursor = _encode_genres_cursor(last_count, last_slug)

        return GenresCatalogPageDTO(items=items, next_cursor=next_cursor)
