from fastapi import APIRouter

from api.auth.routes import router as auth_router
from api.auth.schemas import UserResponse
from deps.auth import CurrentUser
from models.user import User

router = APIRouter(prefix='/api', tags=['api'])

router.include_router(auth_router)


@router.get('/hello')
def api_hello() -> dict[str, str]:
    return {'message': 'Hello from Filmony backend'}


@router.get('/me', response_model=UserResponse)
async def api_me(user: CurrentUser) -> User:
    return user
