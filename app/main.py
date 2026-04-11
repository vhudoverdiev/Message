from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import configure_logging
from app.routes import auth, pages

configure_logging()
app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(auth.router)
app.include_router(pages.router)


@app.on_event('startup')
def on_startup() -> None:
    init_db()
