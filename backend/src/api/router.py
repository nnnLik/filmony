from fastapi import APIRouter

from api.auth.routes import router as auth_router
from api.auth.schemas import UserResponse
from api.cards.routes import router as cards_router
from api.catalog.routes import router as catalog_router
from api.feed.routes import router as feed_router
from api.feed_posts.routes import router as feed_posts_router
from api.films.routes import router as films_router
from api.notifications.routes import router as notifications_router
from api.profile.me_routes import router as profile_me_router
from api.profile.users_routes import router as profile_users_router
from api.reactions.routes import router as reactions_router
from api.search.routes import router as search_router
from api.watchlist.routes import router as watchlist_router
from deps.auth import CurrentUser
from models.user import User

router = APIRouter(prefix='/api', tags=['api'])

router.include_router(auth_router)
router.include_router(cards_router)
router.include_router(catalog_router)
router.include_router(feed_router)
router.include_router(feed_posts_router)
router.include_router(films_router)
router.include_router(reactions_router)
router.include_router(search_router)
router.include_router(notifications_router)
router.include_router(profile_me_router)
router.include_router(profile_users_router)
router.include_router(watchlist_router)


@router.get('/hello')
def api_hello() -> dict[str, str]:
    return {'message': 'Hello from Filmony backend'}


@router.get('/me', response_model=UserResponse)
async def api_me(user: CurrentUser) -> User:
    return user
