from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    _app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    _app.include_router(api_router, prefix=settings.api_v1_prefix)

    return _app


app = create_app()
