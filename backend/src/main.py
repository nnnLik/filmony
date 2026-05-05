import uvicorn
from fastapi import FastAPI

from conf import settings
from utils.app_utils import get_app, setup_app

app: FastAPI = setup_app(get_app())



@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
        workers=settings.app.worker_count,
    )
