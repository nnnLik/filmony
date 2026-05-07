"""Thin HTTP client for Telegram Bot API — infrastructure only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class TelegramSendMessageResult:
    ok: bool
    payload: dict[str, Any]


class TelegramBotApiClient:
    """POST sendMessage / sendPhoto; maps JSON body regardless of HTTP status (Telegram uses 200 + ok:false)."""

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

    async def _post_json(self, url: str, payload: dict[str, object]) -> TelegramSendMessageResult:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload)
        try:
            payload = response.json()
        except Exception:
            payload = {
                'ok': False,
                'description': response.text[:500] if response.text else 'invalid json',
            }
        if not isinstance(payload, dict):
            payload = {'ok': False, 'description': 'unexpected telegram response shape'}
        return TelegramSendMessageResult(ok=bool(payload.get('ok')), payload=payload)
