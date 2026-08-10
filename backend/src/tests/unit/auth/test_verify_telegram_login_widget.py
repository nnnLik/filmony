import time

import pytest

from services.auth.errors import TelegramLoginWidgetInvalidError
from services.auth.verify_telegram_login_widget import VerifyTelegramLoginWidgetService
from tests.auth.telegram_login_widget import build_login_widget_fields

BOT_TOKEN = '123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'


def test_verify_login_widget_valid_signature() -> None:
    fields = build_login_widget_fields(bot_token=BOT_TOKEN, user_id=99, username='u99')
    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    user = svc.execute(
        user_id=int(fields['id']),
        auth_date=int(fields['auth_date']),
        hash_value=fields['hash'],
        first_name=fields.get('first_name'),
        last_name=fields.get('last_name'),
        username=fields.get('username'),
        photo_url=fields.get('photo_url'),
    )
    assert user.telegram_user_id == 99
    assert user.username == 'u99'
    assert user.first_name == 'Test'
    assert user.last_name is None
    assert user.photo_url is None
    assert user.language_code is None


def test_verify_login_widget_wrong_hash() -> None:
    fields = build_login_widget_fields(bot_token=BOT_TOKEN)
    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    with pytest.raises(TelegramLoginWidgetInvalidError, match='hash mismatch'):
        svc.execute(
            user_id=int(fields['id']),
            auth_date=int(fields['auth_date']),
            hash_value='deadbeef',
            first_name=fields.get('first_name'),
            username=fields.get('username'),
        )


def test_verify_login_widget_expired_auth_date() -> None:
    old = int(time.time()) - 200_000
    fields = build_login_widget_fields(bot_token=BOT_TOKEN, auth_date=old)
    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    with pytest.raises(TelegramLoginWidgetInvalidError, match='auth_date out of range'):
        svc.execute(
            user_id=int(fields['id']),
            auth_date=int(fields['auth_date']),
            hash_value=fields['hash'],
            first_name=fields.get('first_name'),
            username=fields.get('username'),
        )


def test_verify_login_widget_missing_hash() -> None:
    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    with pytest.raises(TelegramLoginWidgetInvalidError, match='missing hash'):
        svc.execute(
            user_id=1,
            auth_date=int(time.time()),
            hash_value='',
            first_name='Test',
        )


def test_verify_login_widget_missing_auth_date() -> None:
    fields = build_login_widget_fields(bot_token=BOT_TOKEN)
    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    with pytest.raises(TelegramLoginWidgetInvalidError, match='missing auth_date'):
        svc.execute(
            user_id=int(fields['id']),
            auth_date=None,
            hash_value=fields['hash'],
            first_name=fields.get('first_name'),
            username=fields.get('username'),
        )


def test_verify_login_widget_field_order_independence() -> None:
    auth_date = int(time.time())
    fields_a = build_login_widget_fields(
        bot_token=BOT_TOKEN,
        user_id=7,
        auth_date=auth_date,
        first_name='A',
        last_name='B',
        username='ab',
        photo_url='https://example.com/p.jpg',
    )
    # Re-sign with fields inserted in different order (helper always sorts internally).
    fields_b = build_login_widget_fields(
        bot_token=BOT_TOKEN,
        user_id=7,
        auth_date=auth_date,
        photo_url='https://example.com/p.jpg',
        username='ab',
        last_name='B',
        first_name='A',
    )
    assert fields_a['hash'] == fields_b['hash']

    svc = VerifyTelegramLoginWidgetService(bot_token=BOT_TOKEN)
    user = svc.execute(
        user_id=7,
        auth_date=auth_date,
        hash_value=fields_a['hash'],
        photo_url='https://example.com/p.jpg',
        username='ab',
        last_name='B',
        first_name='A',
    )
    assert user.telegram_user_id == 7
    assert user.photo_url == 'https://example.com/p.jpg'
