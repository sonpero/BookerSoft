import os

# Must be set before bookersoft.config (and anything importing it) loads for
# the first time, since it reads the env var at module import time.
os.environ.setdefault("SESSION_SECRET", "test-secret-not-for-production")

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bookersoft import db
from bookersoft.auth import hash_password
from bookersoft.config import get_books_dir, get_covers_dir
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.db import get_db
from bookersoft.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "books").mkdir()
    (tmp_path / "covers").mkdir()
    return tmp_path


@pytest.fixture
def books_dir(data_dir: Path) -> Path:
    return data_dir / "books"


@pytest.fixture
def covers_dir(data_dir: Path) -> Path:
    return data_dir / "covers"


@pytest.fixture
def db_conn(data_dir: Path):
    conn = db.get_connection(data_dir / "library.db")
    db.init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(data_dir: Path, books_dir: Path, covers_dir: Path, db_conn):
    app = create_app()
    # db_conn is shared across every request TestClient makes in this test,
    # even though each request may run in a different threadpool worker
    # thread (hence check_same_thread=False in get_connection). This is only
    # safe because TestClient is synchronous: each client.*() call blocks
    # until the response completes, so the connection is never touched by
    # two threads at once. Revisit if a test ever issues concurrent requests.
    app.dependency_overrides[get_db] = lambda: db_conn
    app.dependency_overrides[get_books_dir] = lambda: books_dir
    app.dependency_overrides[get_covers_dir] = lambda: covers_dir
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=1, username="owner", is_owner=True
    )

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(data_dir: Path, books_dir: Path, covers_dir: Path, db_conn):
    # Unlike `client`, this does NOT override get_current_user: requests go
    # through the real cookie-based session resolution, for tests that need
    # to exercise login/logout/multi-user behaviour itself.
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_conn
    app.dependency_overrides[get_books_dir] = lambda: books_dir
    app.dependency_overrides[get_covers_dir] = lambda: covers_dir

    # https base_url: the session cookie is Secure, so httpx's cookie jar
    # would silently drop it on subsequent requests over a plain http:// test
    # origin (this is real production behaviour to preserve, not to work around).
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


@pytest.fixture
def create_user(db_conn):
    """Create or update a user with a real password hash, bypassing the CLI."""

    def _create(username: str, password: str, is_owner: bool = False) -> int:
        password_hash = hash_password(password)
        existing = db_conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            cursor = db_conn.execute(
                "INSERT INTO users (username, password_hash, is_owner) VALUES (?, ?, ?)",
                (username, password_hash, int(is_owner)),
            )
            user_id = cursor.lastrowid
        else:
            db_conn.execute(
                "UPDATE users SET password_hash = ?, is_owner = ? WHERE id = ?",
                (password_hash, int(is_owner), existing["id"]),
            )
            user_id = existing["id"]
        db_conn.commit()
        return user_id

    return _create


@pytest.fixture
def login(auth_client):
    def _login(username: str, password: str):
        return auth_client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    return _login


@pytest.fixture(autouse=True)
def _reset_login_rate_limiter():
    # The rate limiter is process-global (keyed by client IP, which TestClient
    # keeps constant across requests), so it must be reset between tests to
    # keep them isolated from each other.
    from bookersoft.auth import _failed_attempts

    _failed_attempts.clear()
    yield
    _failed_attempts.clear()


@pytest.fixture
def valid_epub_bytes() -> bytes:
    return (FIXTURES_DIR / "valid.epub").read_bytes()


@pytest.fixture
def valid_epub_bytes_2() -> bytes:
    return (FIXTURES_DIR / "valid2.epub").read_bytes()


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    return (FIXTURES_DIR / "valid.pdf").read_bytes()


@pytest.fixture
def fake_epub_bytes() -> bytes:
    return (FIXTURES_DIR / "fake.epub").read_bytes()


@pytest.fixture
def epub_full_metadata_bytes() -> bytes:
    return (FIXTURES_DIR / "epub_full_metadata.epub").read_bytes()


@pytest.fixture
def epub_missing_opf_bytes() -> bytes:
    return (FIXTURES_DIR / "epub_missing_opf.epub").read_bytes()


@pytest.fixture
def pdf_full_metadata_bytes() -> bytes:
    return (FIXTURES_DIR / "pdf_full_metadata.pdf").read_bytes()


@pytest.fixture
def epub2_cover_meta_bytes() -> bytes:
    return (FIXTURES_DIR / "epub2_cover_meta.epub").read_bytes()


@pytest.fixture
def epub3_cover_properties_bytes() -> bytes:
    return (FIXTURES_DIR / "epub3_cover_properties.epub").read_bytes()


@pytest.fixture
def epub3_cover_properties_multi_bytes() -> bytes:
    return (FIXTURES_DIR / "epub3_cover_properties_multi.epub").read_bytes()
