from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from core.database import get_db
from models.user import User
from services.auth.decode_session_jwt import DecodeSessionJwtService

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session_cookie: Annotated[
        str | None,
        Cookie(alias=settings.auth_jwt.session_cookie_name),
    ] = None,
) -> User:
    token: str | None = None
    if bearer and bearer.scheme.lower() == 'bearer' and bearer.credentials.strip():
        token = bearer.credentials.strip()
    elif session_cookie and session_cookie.strip():
        token = session_cookie.strip()
    if not token:
        raise HTTPException(status_code=401, detail='not authenticated')
    try:
        uid = DecodeSessionJwtService().execute(token)
    except ValueError:
        raise HTTPException(status_code=401, detail='invalid session') from None

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail='user not found')
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
