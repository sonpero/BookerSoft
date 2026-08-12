from bookersoft import db
from bookersoft.auth import verify_password
from bookersoft.cli import create_or_update_user


def _conn(tmp_path):
    conn = db.get_connection(tmp_path / "library.db")
    db.init_db(conn)
    return conn


def test_create_or_update_user_creates_new_user_with_hashed_password(tmp_path):
    conn = _conn(tmp_path)

    create_or_update_user(conn, "alice", "s3cret", is_owner=False)

    row = conn.execute(
        "SELECT password_hash, is_owner FROM users WHERE username = 'alice'"
    ).fetchone()
    assert row is not None
    assert row["password_hash"] != "s3cret"  # never stored in clear
    assert verify_password(row["password_hash"], "s3cret")
    assert row["is_owner"] == 0


def test_create_or_update_user_with_owner_flag_sets_is_owner(tmp_path):
    conn = _conn(tmp_path)

    create_or_update_user(conn, "alice", "s3cret", is_owner=True)

    row = conn.execute("SELECT is_owner FROM users WHERE username = 'alice'").fetchone()
    assert row["is_owner"] == 1


def test_create_or_update_user_resets_password_for_existing_user(tmp_path):
    conn = _conn(tmp_path)
    create_or_update_user(conn, "alice", "old-password", is_owner=False)

    create_or_update_user(conn, "alice", "new-password", is_owner=False)

    row = conn.execute("SELECT password_hash FROM users WHERE username = 'alice'").fetchone()
    assert verify_password(row["password_hash"], "new-password")
    assert not verify_password(row["password_hash"], "old-password")
    count = conn.execute("SELECT COUNT(*) FROM users WHERE username = 'alice'").fetchone()[0]
    assert count == 1


def test_resetting_password_without_owner_flag_does_not_revoke_ownership(tmp_path):
    conn = _conn(tmp_path)
    create_or_update_user(conn, "owner", "first-password", is_owner=True)

    create_or_update_user(conn, "owner", "second-password", is_owner=False)

    row = conn.execute("SELECT is_owner FROM users WHERE username = 'owner'").fetchone()
    assert row["is_owner"] == 1
