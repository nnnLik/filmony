"""Sign test Telegram Login Widget payloads with the same bot_token as settings."""

from __future__ import annotations

import hashlib
import hmac
import time


def build_login_widget_fields(
    *,
    bot_token: str,
    user_id: int = 42,
    auth_date: int | None = None,
    username: str | None = 'tester',
    first_name: str | None = 'Test',
    last_name: str | None = None,
    photo_url: str | None = None,
) -> dict[str, str]:
    if auth_date is None:
        auth_date = int(time.time())

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
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
    digest = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    fields['hash'] = digest
    return fields
