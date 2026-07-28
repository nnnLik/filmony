import uvicorn
from conf import settings
from fastapi import FastAPI
from utils.app_utils import get_app, setup_app

app: FastAPI = setup_app(get_app())


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
        workers=settings.app.worker_count,
    )
