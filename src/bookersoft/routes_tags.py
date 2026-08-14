import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.models import TagIn, TagOut

router = APIRouter(tags=["tags"])

TAG_COLUMNS = "t.id, t.name, (SELECT COUNT(*) FROM book_tags WHERE tag_id = t.id) AS book_count"


def normalize_tag_name(raw: str) -> str:
    return " ".join(raw.strip().lower().split())


def _row_to_tag(row: sqlite3.Row) -> TagOut:
    return TagOut(id=row["id"], name=row["name"], book_count=row["book_count"])


def _book_exists(db: sqlite3.Connection, book_id: int) -> bool:
    return db.execute("SELECT 1 FROM books WHERE id = ?", (book_id,)).fetchone() is not None


def fetch_tags_for_books(db: sqlite3.Connection, book_ids: list[int]) -> dict[int, list[TagOut]]:
    """One query for all of book_ids: used by the book list endpoint to
    attach each book's tags without an extra query per book."""
    result: dict[int, list[TagOut]] = {book_id: [] for book_id in book_ids}
    if not book_ids:
        return result

    placeholders = ",".join("?" * len(book_ids))
    rows = db.execute(
        f"SELECT bt.book_id, {TAG_COLUMNS} FROM book_tags bt "
        f"JOIN tags t ON t.id = bt.tag_id "
        f"WHERE bt.book_id IN ({placeholders}) ORDER BY t.name",
        book_ids,
    ).fetchall()
    for row in rows:
        result[row["book_id"]].append(_row_to_tag(row))
    return result


def _book_tags(db: sqlite3.Connection, book_id: int) -> list[TagOut]:
    return fetch_tags_for_books(db, [book_id])[book_id]


@router.get("/tags", response_model=list[TagOut])
def list_tags(
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[TagOut]:
    # Returns every tag, unfiltered — the filter bar's multi-select and the
    # add-tag autocomplete both fetch this once and filter client-side, the
    # same way the existing "uploaded by" user list already works. Revisit
    # with a server-side search (a `q` param here) if the tag count ever
    # grows enough for that to matter; for a personal library it doesn't yet.
    rows = db.execute(f"SELECT {TAG_COLUMNS} FROM tags t ORDER BY t.name").fetchall()
    return [_row_to_tag(row) for row in rows]


@router.post("/books/{book_id}/tags", response_model=list[TagOut])
def add_tag_to_book(
    book_id: int,
    payload: TagIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[TagOut]:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    name = normalize_tag_name(payload.name)
    if not name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    db.execute("INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (name,))
    tag_id = db.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()["id"]
    db.execute("INSERT OR IGNORE INTO book_tags (book_id, tag_id) VALUES (?, ?)", (book_id, tag_id))
    db.commit()

    return _book_tags(db, book_id)


@router.delete("/books/{book_id}/tags/{tag_id}", status_code=204)
def remove_tag_from_book(
    book_id: int,
    tag_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    if not _book_exists(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    # Idempotent either way, same stance as adding a tag that's already
    # there: removing one that was never on this book, or is already gone,
    # just leaves things the way the caller wanted them — no error.
    db.execute("DELETE FROM book_tags WHERE book_id = ? AND tag_id = ?", (book_id, tag_id))
    db.commit()
