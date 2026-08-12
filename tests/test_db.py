import hashlib
import sqlite3
from pathlib import Path

import pytest

from bookersoft import db

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_foreign_keys_are_enforced(tmp_path):
    conn = db.get_connection(tmp_path / "library.db")
    db.init_db(conn)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO downloads (book_id, user_id) VALUES (?, ?)",
            (999999, 1),
        )


def test_owner_user_is_seeded(tmp_path):
    conn = db.get_connection(tmp_path / "library.db")
    db.init_db(conn)

    row = conn.execute("SELECT username FROM users WHERE id = 1").fetchone()
    assert row[0] == "owner"


def test_get_db_dependency_enables_foreign_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "library.db")

    gen = db.get_db()
    conn = next(gen)
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        next(gen, None)  # drive the generator past yield, exercising its own conn.close()


def test_pre_milestone2_books_are_backfilled_with_metadata_on_next_init(tmp_path):
    books_dir = tmp_path / "books"
    covers_dir = tmp_path / "covers"
    books_dir.mkdir()
    covers_dir.mkdir()

    # Set up a database shaped like it was left by milestone 1, before the
    # metadata columns existed.
    conn = db.get_connection(tmp_path / "library.db")
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            sha256 TEXT NOT NULL UNIQUE,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            format TEXT NOT NULL CHECK (format IN ('epub', 'pdf')),
            size_bytes INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );
        INSERT INTO users (id, username) VALUES (1, 'owner');
        """
    )
    epub_bytes = (FIXTURES_DIR / "epub_full_metadata.epub").read_bytes()
    sha256 = hashlib.sha256(epub_bytes).hexdigest()
    stored_filename = f"{sha256}.epub"
    (books_dir / stored_filename).write_bytes(epub_bytes)
    conn.execute(
        "INSERT INTO books (user_id, sha256, original_filename, stored_filename, format, size_bytes) "
        "VALUES (1, ?, 'legacy.epub', ?, 'epub', ?)",
        (sha256, stored_filename, len(epub_bytes)),
    )
    conn.commit()
    conn.close()

    # Simulate the app reconnecting to this pre-milestone-2 database, e.g. after an upgrade.
    conn = db.get_connection(tmp_path / "library.db")
    db.init_db(conn, books_dir=books_dir, covers_dir=covers_dir)

    row = conn.execute(
        "SELECT title, title_source, author, cover_filename, search_text FROM books"
    ).fetchone()
    assert row["title"] == "Full Metadata Book"
    assert row["title_source"] == "auto"
    assert row["author"] == "Jane Doe"
    assert row["cover_filename"] is not None
    assert (covers_dir / row["cover_filename"]).exists()
    assert row["search_text"] == "full metadata book jane doe"
