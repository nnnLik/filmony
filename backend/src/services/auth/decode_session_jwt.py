from __future__ import annotations

from uuid import UUID

import jwt
from jwt import InvalidTokenError

from conf import settings


class DecodeSessionJwtService:
    """Validate session JWT and return internal user id."""

    def execute(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                settings.auth_jwt.jwt_secret,
                algorithms=['HS256'],
            )
        except InvalidTokenError as e:
            raise ValueError('invalid session token') from e
        if payload.get('typ') != 'session':
            raise ValueError('unexpected token type')
        sub = payload.get('sub')
        if not sub:
            raise ValueError('missing subject')
        return UUID(str(sub))
