import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.logging import configure_logging
from app.models.channel_account import ChannelAccount
from app.routes import auth, pages
from app.services.channel_service import ChannelService

configure_logging()
app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(auth.router)
app.include_router(pages.router)
sync_task: asyncio.Task | None = None


def run_auto_sync_cycle() -> None:
    db = SessionLocal()
    try:
        service = ChannelService(db)
        for account in db.query(ChannelAccount).filter(ChannelAccount.channel == 'telegram').all():
            service.sync_telegram(account)
        for account in db.query(ChannelAccount).filter(ChannelAccount.channel == 'gmail').all():
            service.sync_gmail(account)
        for account in db.query(ChannelAccount).filter(ChannelAccount.channel == 'vk').all():
            service.sync_vk(account)
    finally:
        db.close()


async def auto_sync_loop() -> None:
    while True:
        await asyncio.to_thread(run_auto_sync_cycle)
        await asyncio.sleep(1)


@app.on_event('startup')
def on_startup() -> None:
    global sync_task
    init_db()
    sync_task = asyncio.create_task(auto_sync_loop())


@app.on_event('shutdown')
async def on_shutdown() -> None:
    global sync_task
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
