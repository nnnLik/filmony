from __future__ import annotations

import time
from uuid import UUID

import jwt

from conf import settings


class IssueSessionJwtService:
    """Create a signed session JWT referencing the internal user id."""

    def execute(self, user_id: UUID) -> str:
        now = int(time.time())
        return jwt.encode(
            {
                'sub': str(user_id),
                'typ': 'session',
                'iat': now,
                'exp': now + settings.auth_jwt.session_max_age_seconds,
            },
            settings.auth_jwt.jwt_secret,
            algorithm='HS256',
        )
