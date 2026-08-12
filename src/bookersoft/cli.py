import argparse
import getpass
import sqlite3

from bookersoft.auth import hash_password
from bookersoft.config import DB_PATH
from bookersoft.db import get_connection, init_db


def create_or_update_user(
    conn: sqlite3.Connection, username: str, password: str, is_owner: bool
) -> None:
    """Create a user, or reset an existing one's password — the same operation
    either way. --owner grants ownership but omitting it never revokes it."""
    password_hash = hash_password(password)
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO users (username, password_hash, is_owner) VALUES (?, ?, ?)",
            (username, password_hash, int(is_owner)),
        )
    else:
        set_parts = ["password_hash = ?"]
        params: list[object] = [password_hash]
        if is_owner:
            set_parts.append("is_owner = 1")
        params.append(username)
        conn.execute(f"UPDATE users SET {', '.join(set_parts)} WHERE username = ?", params)

    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bookersoft-users",
        description="Create a user account, or reset its password if it already exists.",
    )
    parser.add_argument("username")
    parser.add_argument(
        "--owner", action="store_true", help="Grant this account library-owner privileges"
    )
    args = parser.parse_args()

    password = getpass.getpass("New password: ")
    confirm = getpass.getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    if password != confirm:
        raise SystemExit("Passwords do not match.")

    conn = get_connection(DB_PATH)
    init_db(conn)
    create_or_update_user(conn, args.username, password, args.owner)
    conn.close()

    print(f"User '{args.username}' is ready.")


if __name__ == "__main__":
    main()
