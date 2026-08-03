"""Load catalog item metadata for the community hub page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game

CatalogDetailKind = Literal['film', 'game']


@dataclass(frozen=True, slots=True)
class CatalogItemDetailDTO:
    catalog_item_id: int
    provider: CatalogProvider
    external_id: str
    kind: CatalogDetailKind
    title: str
    year: int | None
    poster_url: str | None
    short_description: str | None
    description: str | None
    film_id: int | None
    game_id: int | None
    genres: list[str]


@dataclass
class GetCatalogItemDetailService:
    """Resolves persisted catalog metadata for films and games."""

    _session: AsyncSession

    class CatalogItemNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, catalog_item_id: int) -> CatalogItemDetailDTO:
        item = await self._session.get(CatalogItem, catalog_item_id)
        if item is None:
            raise self.CatalogItemNotFound

        if item.film_id is not None:
            film = await self._session.get(Film, item.film_id)
            if film is None:
                raise self.CatalogItemNotFound
            return CatalogItemDetailDTO(
                catalog_item_id=int(item.id),
                provider=item.provider,
                external_id=item.external_id,
                kind='film',
                title=film.title,
                year=film.year,
                poster_url=film.poster_url,
                short_description=film.short_description,
                description=film.description,
                film_id=int(film.id),
                game_id=None,
                genres=list(film.genres or []),
            )

        if item.game_id is not None:
            game = await self._session.get(Game, item.game_id)
            if game is None:
                raise self.CatalogItemNotFound
            year = _parse_year(game.released)
            return CatalogItemDetailDTO(
                catalog_item_id=int(item.id),
                provider=item.provider,
                external_id=item.external_id,
                kind='game',
                title=game.name or 'Игра',
                year=year,
                poster_url=game.background_image,
                short_description=_game_short_description(game),
                description=game.description,
                film_id=None,
                game_id=int(game.id),
                genres=[],
            )

        raise self.CatalogItemNotFound


def _parse_year(released: str | None) -> int | None:
    if released is None or len(released) < 4:
        return None
    try:
        return int(released[:4])
    except ValueError:
        return None


def _game_short_description(game: Game) -> str | None:
    if game.description:
        text = game.description.strip()
        if len(text) <= 280:
            return text
        return text[:277].rstrip() + '…'
    return None
