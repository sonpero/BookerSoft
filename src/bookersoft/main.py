from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bookersoft.config import STATIC_DIR
from bookersoft.routes_books import router as books_router


def create_app() -> FastAPI:
    app = FastAPI(title="BookerSoft")
    app.include_router(books_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
