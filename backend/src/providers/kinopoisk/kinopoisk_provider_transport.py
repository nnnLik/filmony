from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus
from typing import Any, ClassVar

import httpx

from conf import settings
from providers.shared_async_http import httpx_get_idempotent

from ..base_provider_http_transport import BaseProviderHttpTransport
from .kinopoisk_film_dto import KinopoiskFilmDTO, KinopoiskFilmDtoParseError
from .kinopoisk_search_dto import KinopoiskFilmSearchResponseDTO
from .kinopoisk_sequels_dto import KinopoiskSequelFilmDTO, sequel_films_from_list
from .kinopoisk_staff_dto import KinopoiskStaffMemberDTO, staff_members_from_list


class KinopoiskEndpointEnum(StrEnum):
    V2_2_FILM_BY_ID = '/v2.2/films/{kinopoisk_id}'
    V2_1_FILMS_SEARCH_BY_KEYWORD = '/v2.1/films/search-by-keyword'
    V1_STAFF_BY_FILM_ID = '/v1/staff'
    V2_1_FILMS_SEQUELS_AND_PREQUELS = '/v2.1/films/{kinopoisk_id}/sequels_and_prequels'


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

    async def _get_json_list(
        self,
        *,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
    ) -> list[Any]:
        try:
            response = await httpx_get_idempotent(
                url,
                headers=headers,
                params=params,
            )
        except httpx.HTTPError as exc:
            raise self.ProviderHttpError(msg=str(exc)) from exc

        if response.status_code == HTTPStatus.NOT_FOUND:
            return []

        if response.status_code != HTTPStatus.OK:
            raise self.ProviderUnexpectedStatusError(
                msg=f'unexpected status {response.status_code}',
                status_code=response.status_code,
            )

        try:
            payload_raw = response.json()
        except ValueError as exc:
            raise self.ProviderInvalidJsonError(msg='invalid json response') from exc

        if not isinstance(payload_raw, list):
            raise self.ProviderInvalidJsonRootError(msg='json root must be a list')

        return payload_raw

    async def get_staff_by_film_id(self, kinopoisk_id: int) -> tuple[KinopoiskStaffMemberDTO, ...]:
        """GET ``/v1/staff?filmId={id}`` — cast and crew for a film."""

        try:
            payload = await self._get_json_list(
                url=self._build_url(KinopoiskEndpointEnum.V1_STAFF_BY_FILM_ID),
                headers=self._build_headers(),
                params={'filmId': kinopoisk_id},
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.KinopoiskProviderTransportError from exc
        try:
            return staff_members_from_list(payload)
        except KinopoiskFilmDtoParseError as exc:
            raise self.KinopoiskProviderTransportError from exc

    async def get_sequels_and_prequels(
        self,
        kinopoisk_id: int,
    ) -> tuple[KinopoiskSequelFilmDTO, ...]:
        """GET ``/v2.1/films/{id}/sequels_and_prequels`` — franchise cluster members."""

        try:
            payload = await self._get_json_list(
                url=self._build_url(
                    KinopoiskEndpointEnum.V2_1_FILMS_SEQUELS_AND_PREQUELS.format(
                        kinopoisk_id=kinopoisk_id,
                    ),
                ),
                headers=self._build_headers(),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.KinopoiskProviderTransportError from exc
        try:
            return sequel_films_from_list(payload)
        except KinopoiskFilmDtoParseError as exc:
            raise self.KinopoiskProviderTransportError from exc
