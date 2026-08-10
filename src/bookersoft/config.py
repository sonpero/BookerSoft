import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
BOOKS_DIR = DATA_DIR / "books"
DB_PATH = DATA_DIR / "library.db"


def get_books_dir() -> Path:
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    return BOOKS_DIR
