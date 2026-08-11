import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Depends

from bookersoft.config import DB_PATH, get_books_dir, get_covers_dir
from bookersoft.extraction import apply_extraction

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Added via ALTER TABLE rather than in schema.sql so that databases created
# under milestone 1 (with the base `books` table only) pick them up too.
METADATA_COLUMNS = [
    ("title", "TEXT"),
    ("title_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("author", "TEXT"),
    ("author_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("language", "TEXT"),
    ("language_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("publication_year", "INTEGER"),
    ("publication_year_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("publisher", "TEXT"),
    ("publisher_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("isbn", "TEXT"),
    ("isbn_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("description", "TEXT"),
    ("description_source", "TEXT NOT NULL DEFAULT 'auto'"),
    ("cover_filename", "TEXT"),
    ("extraction_failed", "INTEGER NOT NULL DEFAULT 0"),
    ("needs_attention", "INTEGER NOT NULL DEFAULT 0"),
    ("search_text", "TEXT NOT NULL DEFAULT ''"),
]


# SQLite disables foreign key enforcement by default per connection.
def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_metadata_columns(conn: sqlite3.Connection) -> bool:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(books)")}
    added_any = False
    for name, ddl in METADATA_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE books ADD COLUMN {name} {ddl}")
            added_any = True
    return added_any


def init_db(
    conn: sqlite3.Connection, books_dir: Path | None = None, covers_dir: Path | None = None
) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    just_migrated = _ensure_metadata_columns(conn)
    conn.commit()

    if just_migrated and books_dir is not None and covers_dir is not None:
        book_ids = [row["id"] for row in conn.execute("SELECT id FROM books")]
        for book_id in book_ids:
            apply_extraction(conn, book_id, books_dir, covers_dir)


def get_db(
    books_dir: Path = Depends(get_books_dir),
    covers_dir: Path = Depends(get_covers_dir),
) -> Iterator[sqlite3.Connection]:
    conn = get_connection(DB_PATH)
    init_db(conn, books_dir, covers_dir)
    try:
        yield conn
    finally:
        conn.close()
