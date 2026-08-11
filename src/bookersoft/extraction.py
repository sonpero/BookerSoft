import html
import posixpath
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

METADATA_FIELDS = (
    "title",
    "author",
    "language",
    "publication_year",
    "publisher",
    "isbn",
    "description",
)

CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
OPF_SCHEME_ATTR = f"{{{OPF_NS['opf']}}}scheme"

# Signature-based detection, consistent with how uploaded book files are
# validated: never trust a declared media type or file extension.
IMAGE_SIGNATURES: list[tuple[bytes, str, str]] = [
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
]


@dataclass
class ExtractedMetadata:
    title: str | None = None
    author: str | None = None
    language: str | None = None
    publication_year: int | None = None
    publisher: str | None = None
    isbn: str | None = None
    description: str | None = None
    cover_bytes: bytes | None = None
    cover_extension: str | None = None
    failed: bool = False


def detect_image_type(data: bytes) -> tuple[str, str] | None:
    for signature, media_type, extension in IMAGE_SIGNATURES:
        if data.startswith(signature):
            return media_type, extension
    return None


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _year_from_text(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d{4}", value)
    return int(match.group()) if match else None


def _strip_html(raw: str | None) -> str | None:
    """Extraction-time only: descriptions are often HTML and are never
    rendered as-is, so tags are stripped down to plain text here. Manually
    edited descriptions are never passed through this function."""
    if raw is None:
        return None
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def extract_epub_metadata(file_path: Path) -> ExtractedMetadata:
    try:
        with zipfile.ZipFile(file_path) as archive:
            container = ET.fromstring(archive.read("META-INF/container.xml"))
            rootfile = container.find(".//c:rootfile", CONTAINER_NS)
            opf_path = rootfile.attrib["full-path"]
            opf_root = ET.fromstring(archive.read(opf_path))

            metadata_el = opf_root.find("opf:metadata", OPF_NS)

            def dc_text(tag: str) -> str | None:
                el = metadata_el.find(f"dc:{tag}", OPF_NS)
                return _text(el.text) if el is not None else None

            isbn = None
            for identifier in metadata_el.findall("dc:identifier", OPF_NS):
                if identifier.attrib.get(OPF_SCHEME_ATTR, "").upper() == "ISBN":
                    isbn = _text(identifier.text)
                    break

            cover_id = None
            for meta in metadata_el.findall("opf:meta", OPF_NS):
                if meta.attrib.get("name") == "cover":
                    cover_id = meta.attrib.get("content")
                    break

            cover_bytes = None
            cover_extension = None
            if cover_id:
                manifest = opf_root.find("opf:manifest", OPF_NS)
                href = None
                for item in manifest.findall("opf:item", OPF_NS):
                    if item.attrib.get("id") == cover_id:
                        href = item.attrib.get("href")
                        break
                if href:
                    cover_path = posixpath.normpath(
                        posixpath.join(posixpath.dirname(opf_path), href)
                    )
                    raw = archive.read(cover_path)
                    detected = detect_image_type(raw)
                    if detected:
                        _media_type, cover_extension = detected
                        cover_bytes = raw

            return ExtractedMetadata(
                title=dc_text("title"),
                author=dc_text("creator"),
                language=dc_text("language"),
                publication_year=_year_from_text(dc_text("date")),
                publisher=dc_text("publisher"),
                isbn=isbn,
                description=_strip_html(dc_text("description")),
                cover_bytes=cover_bytes,
                cover_extension=cover_extension,
                failed=False,
            )
    except Exception:
        return ExtractedMetadata(failed=True)


def extract_pdf_metadata(file_path: Path) -> ExtractedMetadata:
    try:
        reader = PdfReader(file_path)
        info = reader.metadata

        cover_bytes = None
        cover_extension = None
        if reader.pages:
            resources = reader.pages[0].get("/Resources") or {}
            xobjects = resources.get("/XObject") or {}
            for ref in xobjects.values():
                xobj = ref.get_object()
                if xobj.get("/Subtype") == "/Image" and xobj.get("/Filter") == "/DCTDecode":
                    detected = detect_image_type(xobj.get_data())
                    if detected:
                        _media_type, cover_extension = detected
                        cover_bytes = xobj.get_data()
                    break

        return ExtractedMetadata(
            title=_text(info.title) if info else None,
            author=_text(info.author) if info else None,
            publication_year=info.creation_date.year if info and info.creation_date else None,
            cover_bytes=cover_bytes,
            cover_extension=cover_extension,
            failed=False,
        )
    except Exception:
        return ExtractedMetadata(failed=True)


def extract_metadata(file_path: Path, book_format: str) -> ExtractedMetadata:
    if book_format == "epub":
        return extract_epub_metadata(file_path)
    return extract_pdf_metadata(file_path)


def normalize_search_text(*parts: str | None) -> str:
    joined = " ".join(part for part in parts if part)
    stripped_accents = unicodedata.normalize("NFKD", joined).encode("ascii", "ignore").decode("ascii")
    return stripped_accents.lower()


def apply_extraction(conn: sqlite3.Connection, book_id: int, books_dir: Path, covers_dir: Path) -> None:
    """Run extraction for a book and write the results to the database.

    Fields whose current source is 'manual' are left untouched. The cover
    file has no manual/auto distinction (manual cover upload is out of
    scope), so it is always replaced by the extraction result.
    """
    columns = ["sha256", "stored_filename", "format", "cover_filename"]
    for field in METADATA_FIELDS:
        columns += [field, f"{field}_source"]
    row = conn.execute(
        f"SELECT {', '.join(columns)} FROM books WHERE id = ?", (book_id,)
    ).fetchone()

    extracted = extract_metadata(books_dir / row["stored_filename"], row["format"])

    final_values = {}
    for field in METADATA_FIELDS:
        if row[f"{field}_source"] == "manual":
            final_values[field] = row[field]
        else:
            final_values[field] = getattr(extracted, field)

    if row["cover_filename"]:
        (covers_dir / row["cover_filename"]).unlink(missing_ok=True)

    cover_filename = None
    if extracted.cover_bytes and extracted.cover_extension:
        cover_filename = f"{row['sha256']}.{extracted.cover_extension}"
        (covers_dir / cover_filename).write_bytes(extracted.cover_bytes)

    needs_attention = extracted.failed or not final_values["title"] or not final_values["author"]
    search_text = normalize_search_text(final_values["title"], final_values["author"])

    set_parts = [f"{field} = ?" for field in METADATA_FIELDS]
    params = [final_values[field] for field in METADATA_FIELDS]
    set_parts += ["cover_filename = ?", "extraction_failed = ?", "needs_attention = ?", "search_text = ?"]
    params += [cover_filename, extracted.failed, needs_attention, search_text, book_id]

    conn.execute(f"UPDATE books SET {', '.join(set_parts)} WHERE id = ?", params)
    conn.commit()
