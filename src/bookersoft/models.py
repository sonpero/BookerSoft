from datetime import datetime
from typing import Literal

from pydantic import BaseModel

BookFormat = Literal["epub", "pdf"]
MetadataSource = Literal["auto", "manual"]


class BookSummary(BaseModel):
    id: int
    original_filename: str
    title: str
    author: str | None
    format: BookFormat
    size_bytes: int
    uploaded_at: datetime
    has_cover: bool
    needs_attention: bool


class UploadedBook(BookSummary):
    duplicate: bool


class RejectedFile(BaseModel):
    filename: str
    reason: str


class UploadResponse(BaseModel):
    uploaded: list[UploadedBook]
    rejected: list[RejectedFile]


class BookDetail(BaseModel):
    id: int
    original_filename: str
    format: BookFormat
    size_bytes: int
    uploaded_at: datetime
    title: str
    title_source: MetadataSource
    author: str | None
    author_source: MetadataSource
    language: str | None
    language_source: MetadataSource
    publication_year: int | None
    publication_year_source: MetadataSource
    publisher: str | None
    publisher_source: MetadataSource
    isbn: str | None
    isbn_source: MetadataSource
    description: str | None
    description_source: MetadataSource
    has_cover: bool
    needs_attention: bool
    extraction_failed: bool


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    language: str | None = None
    publication_year: int | None = None
    publisher: str | None = None
    isbn: str | None = None
    description: str | None = None
