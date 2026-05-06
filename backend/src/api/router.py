from fastapi import APIRouter

from api.auth.routes import router as auth_router
from api.auth.schemas import UserResponse
from api.cards.routes import router as cards_router
from api.films.routes import router as films_router
from api.profile.me_routes import router as profile_me_router
from api.profile.users_routes import router as profile_users_router
from deps.auth import CurrentUser
from models.user import User

router = APIRouter(prefix='/api', tags=['api'])

router.include_router(auth_router)
router.include_router(cards_router)
router.include_router(films_router)
router.include_router(profile_me_router)
router.include_router(profile_users_router)


@router.get('/hello')
def api_hello() -> dict[str, str]:
    return {'message': 'Hello from Filmony backend'}


@router.get('/me', response_model=UserResponse)
async def api_me(user: CurrentUser) -> User:
    return user
