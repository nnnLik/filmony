from __future__ import annotations

from uuid import UUID

import jwt

from conf import settings


class IssueSessionJwtService:
    """Create a signed session JWT referencing the internal user id."""

    def execute(self, user_id: UUID) -> str:
        return jwt.encode(
            {
                "sub": str(user_id),
                "typ": "session",
            },
            settings.auth_jwt.jwt_secret,
            algorithm="HS256",
        )
