import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
BOOKS_DIR = DATA_DIR / "books"
COVERS_DIR = DATA_DIR / "covers"
DB_PATH = DATA_DIR / "library.db"
STATIC_DIR = Path(__file__).parent / "static"

SESSION_SECRET = os.environ.get("SESSION_SECRET")
SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days: personal library, not a bank

MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "100"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def get_books_dir() -> Path:
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    return BOOKS_DIR


def get_covers_dir() -> Path:
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    return COVERS_DIR


def get_max_upload_size_bytes() -> int:
    return MAX_UPLOAD_SIZE_BYTES
