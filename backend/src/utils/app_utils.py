from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import router as api_router
from conf import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from core.database import dispose_engine

    await dispose_engine()


def get_app() -> FastAPI:
    return FastAPI(
        title=settings.app.TITLE,
        version=settings.app.VERSION,
        description=settings.app.DESCRIPTION,
        lifespan=lifespan,
        **settings.app.openapi_config,
    )


def setup_app(app: FastAPI) -> FastAPI:
    cors_kw: dict = {
        'allow_origins': settings.app.CORS_ALLOW_ORIGINS,
        'allow_credentials': settings.app.CORS_ALLOW_CREDENTIALS,
        'allow_methods': settings.app.CORS_ALLOW_METHODS,
        'allow_headers': settings.app.CORS_ALLOW_HEADERS,
    }
    app.add_middleware(CORSMiddleware, **cors_kw)
    app.include_router(api_router)

    @app.get('/')
    def read_root() -> dict[str, str]:
        return {'message': 'Hello, World!'}

    return app
