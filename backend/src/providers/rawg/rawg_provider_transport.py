from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

from conf import settings

from ..base_provider_http_transport import BaseProviderHttpTransport
from .rawg_openapi_dto import (
    RawgGameDtoParseError,
    RawgGameSingleDTO,
    RawgGamesListQueryParams,
    RawgGamesListResponseDTO,
)


class RawgEndpointEnum(StrEnum):
    GAMES = '/games'
    GAME_BY_ID = '/games/{game_id}'


class RawgProviderTransport(BaseProviderHttpTransport):

    class RawgProviderTransportError(Exception):
        pass

    _base_url: ClassVar[str] = settings.rawg.base_url
    _api_key: ClassVar[str] = settings.rawg.api_key

    def _build_url(self, path: str) -> str:
        return f'{self._base_url.rstrip("/")}{path}'

    def _params_with_api_key(self, params: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {'key': self._api_key}
        for key, value in params.items():
            merged[key] = value
        return merged

    async def search_games(self, query: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
        try:
            doc = await self.get(
                url=self._build_url(
                    path=RawgEndpointEnum.GAMES,
                ),
                params=self._params_with_api_key(query.to_params()),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.RawgProviderTransportError from exc
        try:
            return RawgGamesListResponseDTO.from_document(doc)
        except RawgGameDtoParseError as exc:
            raise self.RawgProviderTransportError from exc

    async def get_game(self, game_id: str) -> RawgGameSingleDTO:
        gid = game_id.strip()
        if not gid:
            raise self.RawgProviderTransportError()
        try:
            item = await self.get(
                url=self._build_url(
                    path=RawgEndpointEnum.GAME_BY_ID.format(
                        game_id=gid,
                    ),
                ),
                params=self._params_with_api_key({}),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.RawgProviderTransportError from exc
        try:
            return RawgGameSingleDTO.from_dict(item)
        except RawgGameDtoParseError as exc:
            raise self.RawgProviderTransportError from exc
