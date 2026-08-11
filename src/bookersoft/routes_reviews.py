import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.models import ReviewIn, ReviewOut

router = APIRouter(prefix="/books", tags=["reviews"])

REVIEW_COLUMNS = (
    "reviews.id, reviews.book_id, reviews.user_id, users.username, "
    "reviews.rating, reviews.review_text, reviews.created_at, reviews.updated_at"
)


def _row_to_review(row: sqlite3.Row) -> ReviewOut:
    return ReviewOut(
        id=row["id"],
        book_id=row["book_id"],
        user_id=row["user_id"],
        username=row["username"],
        rating=row["rating"],
        review_text=row["review_text"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _book_exists(db: sqlite3.Connection, book_id: int) -> bool:
    return db.execute("SELECT 1 FROM books WHERE id = ?", (book_id,)).fetchone() is not None


@router.get("/{book_id}/reviews", response_model=list[ReviewOut])
def list_reviews(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[ReviewOut]:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    rows = db.execute(
        f"SELECT {REVIEW_COLUMNS} FROM reviews JOIN users ON users.id = reviews.user_id "
        "WHERE reviews.book_id = ? ORDER BY reviews.updated_at DESC",
        (book_id,),
    ).fetchall()
    return [_row_to_review(row) for row in rows]


@router.get("/{book_id}/review", response_model=ReviewOut)
def get_my_review(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> ReviewOut:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    row = db.execute(
        f"SELECT {REVIEW_COLUMNS} FROM reviews JOIN users ON users.id = reviews.user_id "
        "WHERE reviews.book_id = ? AND reviews.user_id = ?",
        (book_id, current_user.id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No review yet")
    return _row_to_review(row)


@router.put("/{book_id}/review", response_model=ReviewOut)
def set_my_review(
    book_id: int,
    payload: ReviewIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> ReviewOut:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    db.execute(
        "INSERT INTO reviews (book_id, user_id, rating, review_text, updated_at) "
        "VALUES (?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) "
        "ON CONFLICT(user_id, book_id) DO UPDATE SET "
        "rating = excluded.rating, review_text = excluded.review_text, "
        "updated_at = excluded.updated_at",
        (book_id, current_user.id, payload.rating, payload.review_text),
    )
    db.commit()

    row = db.execute(
        f"SELECT {REVIEW_COLUMNS} FROM reviews JOIN users ON users.id = reviews.user_id "
        "WHERE reviews.book_id = ? AND reviews.user_id = ?",
        (book_id, current_user.id),
    ).fetchone()
    return _row_to_review(row)


@router.delete("/{book_id}/review", status_code=204)
def delete_my_review(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    row = db.execute(
        "SELECT id FROM reviews WHERE book_id = ? AND user_id = ?", (book_id, current_user.id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No review yet")

    db.execute("DELETE FROM reviews WHERE id = ?", (row["id"],))
    db.commit()
