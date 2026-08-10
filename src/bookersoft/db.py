import sqlite3
from collections.abc import Iterator
from pathlib import Path

from bookersoft.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


# SQLite disables foreign key enforcement by default per connection.
def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection(DB_PATH)
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()
