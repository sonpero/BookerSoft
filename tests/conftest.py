from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bookersoft import db
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
