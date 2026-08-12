import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, RedirectResponse

from bookersoft.auth import (
    clear_failed_logins,
    create_session_token,
    is_rate_limited,
    record_failed_login,
    verify_password,
)
from bookersoft.config import SESSION_COOKIE_NAME, SESSION_MAX_AGE_SECONDS, STATIC_DIR
from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/login")
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    client_ip = _client_ip(request)

    if is_rate_limited(client_ip):
        return RedirectResponse("/login?error=rate_limited", status_code=303)

    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()

    valid = (
        row is not None
        and row["password_hash"] is not None
        and verify_password(row["password_hash"], password)
    )
    if not valid:
        record_failed_login(client_ip)
        return RedirectResponse("/login?error=1", status_code=303)

    clear_failed_logins(client_ip)
    token = create_session_token(row["id"])
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response
