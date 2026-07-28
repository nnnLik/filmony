from typing import Annotated

from core.database import get_db as get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
