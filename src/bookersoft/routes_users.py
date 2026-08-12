import sqlite3

from fastapi import APIRouter, Depends

from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.models import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[UserOut]:
    rows = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    return [UserOut(id=row["id"], username=row["username"]) for row in rows]
