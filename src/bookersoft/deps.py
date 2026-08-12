import sqlite3

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from bookersoft.auth import read_session_token
from bookersoft.config import SESSION_COOKIE_NAME
from bookersoft.db import get_db


class CurrentUser(BaseModel):
    id: int
    username: str
    is_owner: bool


def _resolve_current_user(request: Request, db: sqlite3.Connection) -> CurrentUser | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return None

    user_id = read_session_token(token)
    if user_id is None:
        return None

    row = db.execute(
        "SELECT id, username, is_owner FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None

    return CurrentUser(id=row["id"], username=row["username"], is_owner=bool(row["is_owner"]))


def get_current_user(
    request: Request, db: sqlite3.Connection = Depends(get_db)
) -> CurrentUser:
    user = _resolve_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_page_session(
    request: Request, db: sqlite3.Connection = Depends(get_db)
) -> CurrentUser:
    # Used only by the two HTML shell routes (/ and /books/{id}): a browser
    # navigation should bounce to the login page instead of showing a bare
    # 401. API routes use get_current_user instead, whose 401 the frontend's
    # fetch wrapper turns into a client-side redirect (for a session that
    # expires mid-use).
    user = _resolve_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user
