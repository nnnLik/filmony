"""Thin HTTP client for Telegram Bot API — infrastructure only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


def _telegram_payload_from_response(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception:
        body = {
            'ok': False,
            'description': response.text[:500] if response.text else 'invalid json',
        }
    if not isinstance(body, dict):
        return {'ok': False, 'description': 'unexpected telegram response shape'}
    return body


@dataclass(frozen=True, slots=True)
class TelegramSendMessageResult:
    ok: bool
    payload: dict[str, Any]


class TelegramBotApiClient:
    """POST sendMessage / sendPhoto / sendDocument; maps JSON body regardless of HTTP status (Telegram uses 200 + ok:false)."""

    def __init__(self, bot_token: str) -> None:
        self._token = bot_token

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> TelegramSendMessageResult:
        url = f'https://api.telegram.org/bot{self._token}/sendMessage'
        payload: dict[str, object] = {'chat_id': chat_id, 'text': text}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        return await self._post_json(url, payload)

    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: str,
        *,
        parse_mode: str | None = None,
    ) -> TelegramSendMessageResult:
        url = f'https://api.telegram.org/bot{self._token}/sendPhoto'
        payload: dict[str, object] = {'chat_id': chat_id, 'photo': photo, 'caption': caption}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        return await self._post_json(url, payload)

    async def send_photo_multipart(
        self,
        chat_id: int,
        photo_bytes: bytes,
        caption: str,
        *,
        filename: str = 'poster.jpg',
        content_type: str = 'image/jpeg',
        parse_mode: str | None = None,
    ) -> TelegramSendMessageResult:
        """Отправка локальных байтов изображения (Telegram не тянет внешний URL сам)."""
        url = f'https://api.telegram.org/bot{self._token}/sendPhoto'
        files = {'photo': (filename, photo_bytes, content_type)}
        data: dict[str, str] = {'chat_id': str(chat_id), 'caption': caption}
        if parse_mode:
            data['parse_mode'] = parse_mode
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, data=data, files=files)
        payload = _telegram_payload_from_response(response)
        return TelegramSendMessageResult(ok=bool(payload.get('ok')), payload=payload)

    async def send_document_multipart(
        self,
        chat_id: int,
        document_bytes: bytes,
        *,
        filename: str = 'export.csv',
        content_type: str = 'text/csv',
        caption: str | None = None,
        parse_mode: str | None = None,
    ) -> TelegramSendMessageResult:
        """Upload a file blob as a Telegram document."""
        url = f'https://api.telegram.org/bot{self._token}/sendDocument'
        files = {'document': (filename, document_bytes, content_type)}
        data: dict[str, str] = {'chat_id': str(chat_id)}
        if caption is not None:
            data['caption'] = caption
        if parse_mode:
            data['parse_mode'] = parse_mode
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, data=data, files=files)
        payload = _telegram_payload_from_response(response)
        return TelegramSendMessageResult(ok=bool(payload.get('ok')), payload=payload)

    async def _post_json(self, url: str, payload: dict[str, object]) -> TelegramSendMessageResult:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload)
        body = _telegram_payload_from_response(response)
        return TelegramSendMessageResult(ok=bool(body.get('ok')), payload=body)
