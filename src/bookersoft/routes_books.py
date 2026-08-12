import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from bookersoft.config import STATIC_DIR, get_books_dir, get_covers_dir
from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user, require_page_session
from bookersoft.extraction import apply_extraction, normalize_search_text
from bookersoft.models import (
    BookDetail,
    BookFormat,
    BookSummary,
    BookUpdate,
    RejectedFile,
    SortOption,
    UploadedBook,
    UploadResponse,
)

router = APIRouter(prefix="/books", tags=["books"])

DETAIL_COLUMNS = (
    "id, original_filename, format, size_bytes, uploaded_at, "
    "title, title_source, author, author_source, language, language_source, "
    "publication_year, publication_year_source, publisher, publisher_source, "
    "isbn, isbn_source, description, description_source, "
    "cover_filename, needs_attention, extraction_failed, "
    "(SELECT AVG(rating) FROM reviews WHERE reviews.book_id = books.id) AS average_rating, "
    "(SELECT COUNT(*) FROM reviews WHERE reviews.book_id = books.id) AS rating_count"
)

# search_text and user_id aren't part of BookSummary/BookDetail, but are
# needed to filter/sort the list query; selecting them from a subquery makes
# them, like average_rating and rating_count, addressable in an outer WHERE
# and ORDER BY (aliases from the SELECT list aren't visible there directly).
LIST_COLUMNS = DETAIL_COLUMNS + ", search_text, user_id"

ORDER_BY_CLAUSES: dict[SortOption, str] = {
    "recent": "uploaded_at DESC, id DESC",
    "title": "title COLLATE NOCASE ASC, id DESC",
    "author": "author COLLATE NOCASE ASC, id DESC",
    "rating": "average_rating IS NULL, average_rating DESC, id DESC",
}


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _detect_format(content: bytes) -> BookFormat | None:
    if content.startswith(b"%PDF"):
        return "pdf"
    if content.startswith(b"PK\x03\x04"):
        return "epub"
    return None


def _row_to_summary(row: sqlite3.Row) -> BookSummary:
    return BookSummary(
        id=row["id"],
        original_filename=row["original_filename"],
        title=row["title"] or row["original_filename"],
        author=row["author"],
        format=row["format"],
        size_bytes=row["size_bytes"],
        uploaded_at=row["uploaded_at"],
        has_cover=row["cover_filename"] is not None,
        needs_attention=bool(row["needs_attention"]),
        average_rating=row["average_rating"],
        rating_count=row["rating_count"],
    )


def _row_to_detail(row: sqlite3.Row) -> BookDetail:
    return BookDetail(
        id=row["id"],
        original_filename=row["original_filename"],
        format=row["format"],
        size_bytes=row["size_bytes"],
        uploaded_at=row["uploaded_at"],
        title=row["title"] or row["original_filename"],
        title_source=row["title_source"],
        author=row["author"],
        author_source=row["author_source"],
        language=row["language"],
        language_source=row["language_source"],
        publication_year=row["publication_year"],
        publication_year_source=row["publication_year_source"],
        publisher=row["publisher"],
        publisher_source=row["publisher_source"],
        isbn=row["isbn"],
        isbn_source=row["isbn_source"],
        description=row["description"],
        description_source=row["description_source"],
        has_cover=row["cover_filename"] is not None,
        needs_attention=bool(row["needs_attention"]),
        extraction_failed=bool(row["extraction_failed"]),
        average_rating=row["average_rating"],
        rating_count=row["rating_count"],
    )


@router.post("", response_model=UploadResponse, status_code=201)
def upload_books(
    files: list[UploadFile] = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
    covers_dir: Path = Depends(get_covers_dir),
) -> UploadResponse:
    uploaded: list[UploadedBook] = []
    rejected: list[RejectedFile] = []

    for file in files:
        filename = file.filename or "unnamed"
        content = file.file.read()
        book_format = _detect_format(content)

        if book_format is None:
            rejected.append(RejectedFile(filename=filename, reason="not a valid EPUB or PDF file"))
            continue

        sha256 = hashlib.sha256(content).hexdigest()
        existing = db.execute(
            f"SELECT {DETAIL_COLUMNS} FROM books WHERE sha256 = ?", (sha256,)
        ).fetchone()

        if existing is not None:
            uploaded.append(
                UploadedBook(**_row_to_summary(existing).model_dump(), duplicate=True)
            )
            continue

        stored_filename = f"{sha256}.{book_format}"
        (books_dir / stored_filename).write_bytes(content)

        cursor = db.execute(
            "INSERT INTO books (user_id, sha256, original_filename, stored_filename, format, size_bytes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (current_user.id, sha256, filename, stored_filename, book_format, len(content)),
        )
        db.commit()

        apply_extraction(db, cursor.lastrowid, books_dir, covers_dir)

        row = db.execute(
            f"SELECT {DETAIL_COLUMNS} FROM books WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        uploaded.append(UploadedBook(**_row_to_summary(row).model_dump(), duplicate=False))

    return UploadResponse(uploaded=uploaded, rejected=rejected)


@router.get("", response_model=list[BookSummary])
def list_books(
    needs_attention: bool | None = None,
    q: str | None = None,
    format: BookFormat | None = None,
    min_rating: float | None = Query(default=None, ge=1, le=5),
    uploaded_by: int | None = None,
    sort: SortOption = "recent",
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[BookSummary]:
    conditions: list[str] = []
    params: list[object] = []

    if needs_attention is not None:
        conditions.append("needs_attention = ?")
        params.append(1 if needs_attention else 0)
    if q:
        conditions.append("search_text LIKE ? ESCAPE '\\'")
        params.append(f"%{_escape_like(normalize_search_text(q))}%")
    if format is not None:
        conditions.append("format = ?")
        params.append(format)
    if min_rating is not None:
        conditions.append("average_rating IS NOT NULL AND average_rating >= ?")
        params.append(min_rating)
    if uploaded_by is not None:
        conditions.append("user_id = ?")
        params.append(uploaded_by)

    query = f"SELECT * FROM (SELECT {LIST_COLUMNS} FROM books)"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" ORDER BY {ORDER_BY_CLAUSES[sort]}"

    rows = db.execute(query, params).fetchall()
    return [_row_to_summary(row) for row in rows]


@router.get("/{book_id}/file")
def download_book(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
) -> FileResponse:
    row = db.execute(
        "SELECT stored_filename, original_filename, format FROM books WHERE id = ?",
        (book_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    media_type = "application/epub+zip" if row["format"] == "epub" else "application/pdf"
    ascii_fallback = row["original_filename"].encode("ascii", "replace").decode("ascii")
    encoded_filename = quote(row["original_filename"])
    content_disposition = (
        f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'
    )

    db.execute(
        "INSERT INTO downloads (book_id, user_id) VALUES (?, ?)",
        (book_id, current_user.id),
    )
    db.commit()

    return FileResponse(
        path=books_dir / row["stored_filename"],
        media_type=media_type,
        headers={"Content-Disposition": content_disposition},
    )


@router.get("/{book_id}/cover")
def book_cover(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    covers_dir: Path = Depends(get_covers_dir),
) -> FileResponse:
    row = db.execute("SELECT cover_filename FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None or row["cover_filename"] is None:
        raise HTTPException(status_code=404, detail="This book has no cover")

    cover_path = covers_dir / row["cover_filename"]
    media_type = "image/png" if cover_path.suffix == ".png" else "image/jpeg"
    return FileResponse(path=cover_path, media_type=media_type)


@router.get("/{book_id}/metadata", response_model=BookDetail)
def get_book_metadata(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> BookDetail:
    row = db.execute(f"SELECT {DETAIL_COLUMNS} FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return _row_to_detail(row)


@router.patch("/{book_id}/metadata", response_model=BookDetail)
def update_book_metadata(
    book_id: int,
    payload: BookUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> BookDetail:
    row = db.execute(f"SELECT {DETAIL_COLUMNS} FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        set_parts: list[str] = []
        params: list[object] = []
        for field, value in updates.items():
            set_parts.append(f"{field} = ?")
            params.append(value)
            set_parts.append(f"{field}_source = ?")
            params.append("manual")

        merged = dict(row)
        merged.update(updates)
        needs_attention = bool(merged["extraction_failed"]) or not merged["title"] or not merged["author"]
        search_text = normalize_search_text(merged["title"], merged["author"])
        set_parts += ["needs_attention = ?", "search_text = ?"]
        params += [needs_attention, search_text]

        params.append(book_id)
        db.execute(f"UPDATE books SET {', '.join(set_parts)} WHERE id = ?", params)
        db.commit()

    updated_row = db.execute(f"SELECT {DETAIL_COLUMNS} FROM books WHERE id = ?", (book_id,)).fetchone()
    return _row_to_detail(updated_row)


@router.post("/{book_id}/re-extract", response_model=BookDetail)
def re_extract_book(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
    covers_dir: Path = Depends(get_covers_dir),
) -> BookDetail:
    row = db.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    apply_extraction(db, book_id, books_dir, covers_dir)

    updated_row = db.execute(f"SELECT {DETAIL_COLUMNS} FROM books WHERE id = ?", (book_id,)).fetchone()
    return _row_to_detail(updated_row)


@router.get("/{book_id}")
def book_detail_page(
    book_id: int, current_user: CurrentUser = Depends(require_page_session)
) -> FileResponse:
    # Always serve the SPA shell, even for an unknown id: the page's own JS
    # fetches /books/{id}/metadata and renders the "not found" state itself,
    # rather than the browser showing a raw JSON error response.
    return FileResponse(STATIC_DIR / "index.html")


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
    covers_dir: Path = Depends(get_covers_dir),
) -> None:
    row = db.execute(
        "SELECT stored_filename, cover_filename, user_id FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not (current_user.is_owner or row["user_id"] == current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to delete this book")

    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()

    (books_dir / row["stored_filename"]).unlink(missing_ok=True)
    if row["cover_filename"]:
        (covers_dir / row["cover_filename"]).unlink(missing_ok=True)
