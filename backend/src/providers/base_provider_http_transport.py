from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, ClassVar

import httpx

from providers.shared_async_http import httpx_get_idempotent


class BaseProviderHttpTransport:
    TIMEOUT_SECONDS: ClassVar[float] = 8.0

    @dataclass(slots=True, frozen=True)
    class ProviderHttpError(Exception):
        msg: str

    @dataclass(slots=True, frozen=True)
    class ProviderUnexpectedStatusError(ProviderHttpError):
        status_code: HTTPStatus

    @dataclass(slots=True, frozen=True)
    class ProviderInvalidJsonError(ProviderHttpError):
        pass

    @dataclass(slots=True, frozen=True)
    class ProviderInvalidJsonRootError(ProviderHttpError):
        pass

    def _json_dict_from_response(
        self,
        response: httpx.Response,
    ) -> dict[str, Any]:
        if response.status_code != HTTPStatus.OK:
            raise self.ProviderUnexpectedStatusError(
                msg=f'unexpected status {response.status_code}',
                status_code=response.status_code,
            )

        try:
            payload_raw = response.json()
        except ValueError as exc:
            raise self.ProviderInvalidJsonError(
                msg='invalid json response',
            ) from exc

        if not isinstance(payload_raw, dict):
            raise self.ProviderInvalidJsonRootError(
                msg='json root must be an object',
            )

        return payload_raw

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await httpx_get_idempotent(
                url,
                headers=headers,
                params=params,
            )
        except httpx.HTTPError as exc:
            raise self.ProviderHttpError(msg=str(exc)) from exc

        return self._json_dict_from_response(response)
