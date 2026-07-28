import time
from uuid import uuid4

import jwt
import pytest

from conf import settings
from services.auth.decode_session_jwt import DecodeSessionJwtService
from services.auth.issue_session_jwt import IssueSessionJwtService


def test_issue_session_jwt_includes_exp_claim() -> None:
    user_id = uuid4()
    before = int(time.time())
    token = IssueSessionJwtService().execute(user_id)
    payload = jwt.decode(
        token,
        settings.auth_jwt.jwt_secret,
        algorithms=['HS256'],
    )
    assert payload['sub'] == str(user_id)
    assert payload['typ'] == 'session'
    assert isinstance(payload['iat'], int)
    assert isinstance(payload['exp'], int)
    assert payload['exp'] > payload['iat']
    assert payload['exp'] - payload['iat'] == settings.auth_jwt.session_max_age_seconds
    assert payload['iat'] >= before


def test_decode_session_jwt_rejects_expired_token() -> None:
    user_id = uuid4()
    token = jwt.encode(
        {
            'sub': str(user_id),
            'typ': 'session',
            'exp': int(time.time()) - 60,
        },
        settings.auth_jwt.jwt_secret,
        algorithm='HS256',
    )
    with pytest.raises(ValueError, match='invalid session token'):
        DecodeSessionJwtService().execute(token)


def test_decode_session_jwt_round_trip() -> None:
    user_id = uuid4()
    token = IssueSessionJwtService().execute(user_id)
    assert DecodeSessionJwtService().execute(token) == user_id
