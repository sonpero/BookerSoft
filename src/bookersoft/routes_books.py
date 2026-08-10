import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from bookersoft.config import get_books_dir
from bookersoft.db import get_db
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.models import BookFormat, BookOut, RejectedFile, UploadedBook, UploadResponse

router = APIRouter(prefix="/books", tags=["books"])


def _detect_format(content: bytes) -> BookFormat | None:
    if content.startswith(b"%PDF"):
        return "pdf"
    if content.startswith(b"PK\x03\x04"):
        return "epub"
    return None


@router.post("", response_model=UploadResponse, status_code=201)
def upload_books(
    files: list[UploadFile] = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
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
            "SELECT id, original_filename, format, size_bytes, uploaded_at "
            "FROM books WHERE sha256 = ?",
            (sha256,),
        ).fetchone()

        if existing is not None:
            uploaded.append(UploadedBook(**dict(existing), duplicate=True))
            continue

        stored_filename = f"{sha256}.{book_format}"
        (books_dir / stored_filename).write_bytes(content)

        cursor = db.execute(
            "INSERT INTO books (user_id, sha256, original_filename, stored_filename, format, size_bytes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (current_user.id, sha256, filename, stored_filename, book_format, len(content)),
        )
        db.commit()

        row = db.execute(
            "SELECT id, original_filename, format, size_bytes, uploaded_at FROM books WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        uploaded.append(UploadedBook(**dict(row), duplicate=False))

    return UploadResponse(uploaded=uploaded, rejected=rejected)


@router.get("", response_model=list[BookOut])
def list_books(
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[BookOut]:
    rows = db.execute(
        "SELECT id, original_filename, format, size_bytes, uploaded_at "
        "FROM books ORDER BY uploaded_at DESC, id DESC"
    ).fetchall()
    return [BookOut(**dict(row)) for row in rows]


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


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
    books_dir: Path = Depends(get_books_dir),
) -> None:
    row = db.execute("SELECT stored_filename FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()

    (books_dir / row["stored_filename"]).unlink(missing_ok=True)
