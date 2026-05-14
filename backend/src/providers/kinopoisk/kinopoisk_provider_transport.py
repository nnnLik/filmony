from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus
from typing import ClassVar

from conf import settings

from ..base_provider_http_transport import BaseProviderHttpTransport
from .kinopoisk_film_dto import KinopoiskFilmDTO, KinopoiskFilmDtoParseError
from .kinopoisk_search_dto import KinopoiskFilmSearchResponseDTO


class KinopoiskEndpointEnum(StrEnum):
    V2_2_FILM_BY_ID = '/v2.2/films/{kinopoisk_id}'
    V2_1_FILMS_SEARCH_BY_KEYWORD = '/v2.1/films/search-by-keyword'


class KinopoiskProviderTransport(BaseProviderHttpTransport):

    class KinopoiskProviderTransportError(Exception):
        pass

    _base_url: ClassVar[str] = settings.kinopoisk.base_url
    _api_key: ClassVar[str] = settings.kinopoisk.api_key

    def _build_url(self, path: str) -> str:
        return f'{self._base_url.rstrip("/")}{path}'

    def _build_headers(self) -> dict[str, str]:
        return {'X-API-KEY': self._api_key}

    async def get_film_by_id(self, kinopoisk_id: int) -> KinopoiskFilmDTO:
        try:
            payload = await self.get(
                url=self._build_url(
                    path=KinopoiskEndpointEnum.V2_2_FILM_BY_ID.format(
                        kinopoisk_id=kinopoisk_id,
                    ),
                ),
                headers=self._build_headers(),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.KinopoiskProviderTransportError from exc
        try:
            return KinopoiskFilmDTO.from_dict(payload)
        except KinopoiskFilmDtoParseError as exc:
            raise self.KinopoiskProviderTransportError from exc

    async def search_films_by_keyword(
        self,
        keyword: str,
        page: int = 1,
    ) -> KinopoiskFilmSearchResponseDTO:
        """GET ``/v2.1/films/search-by-keyword`` — Keyword search with pagination (strict API rate limit)."""

        norm = keyword.strip()
        if not norm:
            return KinopoiskFilmSearchResponseDTO.empty(norm)

        try:
            payload = await self.get(
                url=self._build_url(KinopoiskEndpointEnum.V2_1_FILMS_SEARCH_BY_KEYWORD),
                headers=self._build_headers(),
                params={'keyword': norm, 'page': page},
            )
        except BaseProviderHttpTransport.ProviderUnexpectedStatusError as exc:
            if int(exc.status_code) == HTTPStatus.NOT_FOUND:
                return KinopoiskFilmSearchResponseDTO.empty(norm)
            raise self.KinopoiskProviderTransportError from exc
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.KinopoiskProviderTransportError from exc
        try:
            return KinopoiskFilmSearchResponseDTO.from_dict(payload)
        except KinopoiskFilmDtoParseError as exc:
            raise self.KinopoiskProviderTransportError from exc
