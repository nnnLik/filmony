"""Подпись тестового initData под тем же bot_token, что в настройках."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode


def build_init_data(
    *,
    bot_token: str,
    user_id: int = 42,
    auth_date: int | None = None,
    username: str | None = 'tester',
) -> str:
    if auth_date is None:
        auth_date = int(time.time())
    user_obj: dict = {'id': user_id, 'first_name': 'Test', 'username': username}
    user_json = json.dumps(user_obj, separators=(',', ':'))
    pairs = [('auth_date', str(auth_date)), ('user', user_json)]
    pairs.sort(key=lambda x: x[0])
    data_check_string = '\n'.join(f'{k}={v}' for k, v in pairs)
    secret_key = hmac.new(bot_token.encode('utf-8'), b'WebAppData', hashlib.sha256).digest()
    digest = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    out = dict(pairs)
    out['hash'] = digest
    return urlencode(out)
