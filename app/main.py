from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router as api_router
from core.config import settings

app = FastAPI(title=settings.project_name)

app.include_router(api_router, prefix="/api")

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/")
def read_index() -> FileResponse:
    """Отдаем главную HTML-страницу приложения."""
    return FileResponse(settings.static_dir / "index.html")
