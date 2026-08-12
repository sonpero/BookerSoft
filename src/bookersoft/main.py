from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bookersoft.config import STATIC_DIR
from bookersoft.deps import CurrentUser, require_page_session
from bookersoft.routes_auth import router as auth_router
from bookersoft.routes_books import router as books_router
from bookersoft.routes_reviews import router as reviews_router
from bookersoft.routes_users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="BookerSoft")
    app.include_router(auth_router)
    app.include_router(books_router)
    app.include_router(reviews_router)
    app.include_router(users_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index(current_user: CurrentUser = Depends(require_page_session)) -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
