import sqlite3

import pytest

from bookersoft import db


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
