from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bookersoft import db
from bookersoft.config import get_books_dir
from bookersoft.deps import CurrentUser, get_current_user
from bookersoft.db import get_db
from bookersoft.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "books").mkdir()
    return tmp_path


@pytest.fixture
def books_dir(data_dir: Path) -> Path:
    return data_dir / "books"


@pytest.fixture
def db_conn(data_dir: Path):
    conn = db.get_connection(data_dir / "library.db")
    db.init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(data_dir: Path, books_dir: Path, db_conn):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_conn
    app.dependency_overrides[get_books_dir] = lambda: books_dir
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=1, username="owner")

    with TestClient(app) as test_client:
        yield test_client


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
