from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus
from typing import Any, ClassVar

from conf import settings

from ..base_provider_http_transport import BaseProviderHttpTransport
from .tmdb_credits_dto import TmdbDtoParseError
from .tmdb_find_dto import (
    TmdbFindResponseDTO,
    find_response_from_dict,
    search_response_from_dict,
)
from .tmdb_movie_dto import TmdbMovieDetailDTO, movie_detail_from_dict


class TmdbEndpointEnum(StrEnum):
    FIND_BY_EXTERNAL_ID = '/find/{external_id}'
    MOVIE_BY_ID = '/movie/{movie_id}'
    SEARCH_MOVIE = '/search/movie'


class TmdbProviderTransport(BaseProviderHttpTransport):
    class TmdbProviderTransportError(Exception):
        pass

    _base_url: ClassVar[str] = settings.tmdb.base_url
    _api_key: ClassVar[str] = settings.tmdb.api_key
    _read_access_token: ClassVar[str | None] = settings.tmdb.read_access_token
    _language: ClassVar[str] = settings.tmdb.language

    def _build_url(self, path: str) -> str:
        return f'{self._base_url.rstrip("/")}{path}'

    def _build_headers(self) -> dict[str, str]:
        if self._read_access_token:
            return {'Authorization': f'Bearer {self._read_access_token}'}
        return {}

    def _params_with_defaults(self, params: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {'language': self._language}
        if not self._read_access_token:
            merged['api_key'] = self._api_key
        for key, value in params.items():
            merged[key] = value
        return merged

    async def find_movie_by_imdb_id(self, imdb_id: str) -> TmdbFindResponseDTO:
        norm = imdb_id.strip()
        if norm == '':
            return TmdbFindResponseDTO.empty()
        try:
            payload = await self.get(
                url=self._build_url(
                    TmdbEndpointEnum.FIND_BY_EXTERNAL_ID.format(external_id=norm),
                ),
                headers=self._build_headers(),
                params=self._params_with_defaults({'external_source': 'imdb_id'}),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.TmdbProviderTransportError from exc
        try:
            return find_response_from_dict(payload)
        except TmdbDtoParseError as exc:
            raise self.TmdbProviderTransportError from exc

    async def search_movie_by_title_year(
        self,
        title: str,
        year: int | None,
    ) -> TmdbFindResponseDTO:
        norm = title.strip()
        if norm == '':
            return TmdbFindResponseDTO.empty()
        params: dict[str, Any] = {'query': norm}
        if year is not None:
            params['year'] = year
        try:
            payload = await self.get(
                url=self._build_url(TmdbEndpointEnum.SEARCH_MOVIE),
                headers=self._build_headers(),
                params=self._params_with_defaults(params),
            )
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.TmdbProviderTransportError from exc
        try:
            return search_response_from_dict(payload)
        except TmdbDtoParseError as exc:
            raise self.TmdbProviderTransportError from exc

    async def get_movie_by_id(
        self,
        tmdb_id: int,
        *,
        append: tuple[str, ...] = ('credits', 'external_ids'),
    ) -> TmdbMovieDetailDTO:
        params: dict[str, Any] = {}
        if append:
            params['append_to_response'] = ','.join(append)
        try:
            payload = await self.get(
                url=self._build_url(
                    TmdbEndpointEnum.MOVIE_BY_ID.format(movie_id=tmdb_id),
                ),
                headers=self._build_headers(),
                params=self._params_with_defaults(params),
            )
        except BaseProviderHttpTransport.ProviderUnexpectedStatusError as exc:
            if int(exc.status_code) == HTTPStatus.NOT_FOUND:
                raise self.TmdbProviderTransportError('movie not found') from exc
            raise self.TmdbProviderTransportError from exc
        except BaseProviderHttpTransport.ProviderHttpError as exc:
            raise self.TmdbProviderTransportError from exc
        try:
            return movie_detail_from_dict(payload)
        except TmdbDtoParseError as exc:
            raise self.TmdbProviderTransportError from exc


__all__ = ('TmdbProviderTransport',)
