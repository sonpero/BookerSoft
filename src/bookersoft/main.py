from fastapi import FastAPI

from bookersoft.routes_books import router as books_router


def create_app() -> FastAPI:
    app = FastAPI(title="BookerSoft")
    app.include_router(books_router)
    return app


app = create_app()
