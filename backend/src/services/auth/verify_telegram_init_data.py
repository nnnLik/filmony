from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from services.auth.dto import TelegramWebAppUser
from services.auth.errors import TelegramInitDataInvalidError


class VerifyTelegramInitDataService:
    """Verify Telegram Mini App initData per https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app"""

    def __init__(self, *, bot_token: str, max_age_seconds: int = 86400) -> None:
        self._bot_token = bot_token
        self._max_age_seconds = max_age_seconds

    def execute(self, init_data: str) -> TelegramWebAppUser:
        if not init_data or not init_data.strip():
            raise TelegramInitDataInvalidError('empty initData')

        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
        data: dict[str, str] = dict(pairs)
        received_hash = data.pop('hash', None)
        if not received_hash:
            raise TelegramInitDataInvalidError('missing hash')

        auth_date_raw = data.get('auth_date')
        if not auth_date_raw:
            raise TelegramInitDataInvalidError('missing auth_date')
        try:
            auth_date = int(auth_date_raw)
        except ValueError as e:
            raise TelegramInitDataInvalidError('invalid auth_date') from e

        now = int(time.time())
        if now - auth_date > self._max_age_seconds or auth_date > now + 60:
            raise TelegramInitDataInvalidError('auth_date out of range')

        data_check_string = '\n'.join(f'{k}={data[k]}' for k in sorted(data.keys()))
        secret_key = hmac.new(
            self._bot_token.encode('utf-8'),
            b'WebAppData',
            hashlib.sha256,
        ).digest()
        calculated = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated, received_hash):
            raise TelegramInitDataInvalidError('hash mismatch')

        user_raw = data.get('user')
        if not user_raw:
            raise TelegramInitDataInvalidError('missing user')

        try:
            payload = json.loads(user_raw)
        except json.JSONDecodeError as e:
            raise TelegramInitDataInvalidError('invalid user json') from e

        try:
            tid = int(payload['id'])
        except (KeyError, TypeError, ValueError) as e:
            raise TelegramInitDataInvalidError('invalid user id') from e

        return TelegramWebAppUser(
            telegram_user_id=tid,
            username=payload.get('username'),
            first_name=payload.get('first_name'),
            last_name=payload.get('last_name'),
            photo_url=payload.get('photo_url'),
            language_code=payload.get('language_code'),
        )
