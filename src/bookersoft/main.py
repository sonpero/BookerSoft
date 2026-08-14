import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bookersoft.config import STATIC_DIR
from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, require_page_session
from bookersoft.routes_auth import router as auth_router
from bookersoft.routes_books import router as books_router
from bookersoft.routes_reviews import router as reviews_router
from bookersoft.routes_tags import router as tags_router
from bookersoft.routes_users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title="BookerSoft")
    app.include_router(auth_router)
    app.include_router(books_router)
    app.include_router(reviews_router)
    app.include_router(tags_router)
    app.include_router(users_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index(current_user: CurrentUser = Depends(require_page_session)) -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    # Registered last so every route above (API and static) is tried first.
    # Anything left over is either a React Router path (e.g. /upload) that
    # only exists client-side, or a bogus/malicious path that never matched
    # anything real (typo'd endpoint, path-traversal probe). A real browser
    # navigation always sends "text/html" in Accept; a JSON API caller (or a
    # bare request with no meaningful Accept header, like a probe) doesn't.
    # That's what tells the two apart, so new screens don't need a matching
    # route here just to be reachable directly, while unmatched API-shaped
    # requests still 404 as JSON instead of silently returning the shell.
    @app.get("/{full_path:path}")
    def spa_shell(
        full_path: str, request: Request, db: sqlite3.Connection = Depends(get_db)
    ) -> FileResponse:
        if "text/html" not in request.headers.get("accept", ""):
            raise HTTPException(status_code=404, detail="Not Found")
        require_page_session(request, db)
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
