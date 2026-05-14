from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, TypeVar

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


_TDoc = TypeVar('_TDoc')


class RawgProviderTransport(BaseProviderHttpTransport):
    @dataclass(slots=True, frozen=True)
    class RawgProviderTransportError(Exception):
        """Wraps RAWG HTTP or parse failures with a safe, user-visible message."""

        msg: str

        def __str__(self) -> str:
            return self.msg

    _SEARCH_OPERATION = 'RAWG games search'
    _GAME_DETAIL_OPERATION = 'RAWG game detail'

    _base_url: ClassVar[str] = settings.rawg.base_url
    _api_key: ClassVar[str] = settings.rawg.api_key

    def _build_url(self, path: str) -> str:
        return f'{self._base_url.rstrip("/")}{path}'

    def _params_with_api_key(self, params: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {'key': self._api_key}
        for key, value in params.items():
            merged[key] = value
        return merged

    def _safe_http_failure_message(
        self, operation: str, exc: BaseProviderHttpTransport.ProviderHttpError
    ) -> str:
        if isinstance(exc, BaseProviderHttpTransport.ProviderUnexpectedStatusError):
            return f'{operation}: {exc.msg}'
        if isinstance(
            exc,
            (
                BaseProviderHttpTransport.ProviderInvalidJsonError,
                BaseProviderHttpTransport.ProviderInvalidJsonRootError,
            ),
        ):
            return f'{operation}: {exc.msg}'
        return f'{operation}: upstream request failed ({type(exc).__name__})'

    async def _fetch_json_then_parse_document(
        self,
        *,
        operation: str,
        parse_response_label: str,
        fetch_document: Callable[[], Awaitable[dict[str, Any]]],
        parse_document: Callable[[dict[str, Any]], _TDoc],
    ) -> _TDoc:
        try:
            doc = await fetch_document()
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.RawgProviderTransportError(
                msg=self._safe_http_failure_message(operation, exc),
            ) from exc
        try:
            return parse_document(doc)
        except RawgGameDtoParseError as exc:
            raise self.RawgProviderTransportError(
                msg=f'{operation}: failed to parse RAWG {parse_response_label} response ({exc})',
            ) from exc

    async def search_games(self, query: RawgGamesListQueryParams) -> RawgGamesListResponseDTO:
        return await self._fetch_json_then_parse_document(
            operation=self._SEARCH_OPERATION,
            parse_response_label='games search',
            fetch_document=lambda: self.get(
                url=self._build_url(path=RawgEndpointEnum.GAMES),
                params=self._params_with_api_key(query.to_params()),
            ),
            parse_document=RawgGamesListResponseDTO.from_document,
        )

    async def get_game(self, game_id: str) -> RawgGameSingleDTO:
        gid = game_id.strip()
        if not gid:
            raise self.RawgProviderTransportError(
                msg=f'{self._GAME_DETAIL_OPERATION}: game id is empty'
            )
        return await self._fetch_json_then_parse_document(
            operation=self._GAME_DETAIL_OPERATION,
            parse_response_label='game',
            fetch_document=lambda: self.get(
                url=self._build_url(
                    path=RawgEndpointEnum.GAME_BY_ID.format(game_id=gid),
                ),
                params=self._params_with_api_key({}),
            ),
            parse_document=RawgGameSingleDTO.from_dict,
        )
