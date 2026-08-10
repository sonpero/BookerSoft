from datetime import datetime
from typing import Literal

from pydantic import BaseModel

BookFormat = Literal["epub", "pdf"]


class BookOut(BaseModel):
    id: int
    original_filename: str
    format: BookFormat
    size_bytes: int
    uploaded_at: datetime


class UploadedBook(BookOut):
    duplicate: bool


class RejectedFile(BaseModel):
    filename: str
    reason: str


class UploadResponse(BaseModel):
    uploaded: list[UploadedBook]
    rejected: list[RejectedFile]
