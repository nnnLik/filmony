from __future__ import annotations

import hashlib
import hmac
import time

from services.auth.dto import TelegramWebAppUser
from services.auth.errors import TelegramLoginWidgetInvalidError


class VerifyTelegramLoginWidgetService:
    """Verify Telegram Login Widget callback per https://core.telegram.org/widgets/login#checking-authorization"""

    def __init__(self, *, bot_token: str, max_age_seconds: int = 86400) -> None:
        self._bot_token = bot_token
        self._max_age_seconds = max_age_seconds

    def execute(
        self,
        *,
        user_id: int,
        auth_date: int | None,
        hash_value: str | None,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
        photo_url: str | None = None,
    ) -> TelegramWebAppUser:
        if not hash_value:
            raise TelegramLoginWidgetInvalidError('missing hash')
        if auth_date is None:
            raise TelegramLoginWidgetInvalidError('missing auth_date')

        now = int(time.time())
        if now - auth_date > self._max_age_seconds or auth_date > now + 60:
            raise TelegramLoginWidgetInvalidError('auth_date out of range')

        fields: dict[str, str] = {
            'id': str(user_id),
            'auth_date': str(auth_date),
        }
        if first_name is not None:
            fields['first_name'] = first_name
        if last_name is not None:
            fields['last_name'] = last_name
        if username is not None:
            fields['username'] = username
        if photo_url is not None:
            fields['photo_url'] = photo_url

        data_check_string = '\n'.join(f'{k}={fields[k]}' for k in sorted(fields.keys()))
        secret_key = hashlib.sha256(self._bot_token.encode('utf-8')).digest()
        calculated = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated, hash_value):
            raise TelegramLoginWidgetInvalidError('hash mismatch')

        return TelegramWebAppUser(
            telegram_user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
            language_code=None,
        )
