def _upload_and_get_metadata(client, filename, content, content_type):
    upload = client.post(
        "/books", files={"files": (filename, content, content_type)}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    return client.get(f"/books/{book_id}/metadata").json()


def test_epub_metadata_is_extracted_on_upload(client, epub_full_metadata_bytes):
    metadata = _upload_and_get_metadata(
        client, "book.epub", epub_full_metadata_bytes, "application/epub+zip"
    )

    assert metadata["title"] == "Full Metadata Book"
    assert metadata["title_source"] == "auto"
    assert metadata["author"] == "Jane Doe"
    assert metadata["author_source"] == "auto"
    assert metadata["language"] == "fr"
    assert metadata["publication_year"] == 2015
    assert metadata["publisher"] == "Test Publisher"
    assert metadata["isbn"] == "978-3-16-148410-0"
    assert metadata["needs_attention"] is False
    assert metadata["extraction_failed"] is False


def test_epub_cover_is_extracted_and_saved(client, covers_dir, epub_full_metadata_bytes):
    metadata = _upload_and_get_metadata(
        client, "book.epub", epub_full_metadata_bytes, "application/epub+zip"
    )

    assert metadata["has_cover"] is True
    assert len(list(covers_dir.iterdir())) == 1

    cover_response = client.get(f"/books/{metadata['id']}/cover")
    assert cover_response.status_code == 200
    assert cover_response.headers["content-type"] == "image/jpeg"
    assert cover_response.content


def test_book_without_cover_reference_has_no_cover(client, valid_epub_bytes):
    metadata = _upload_and_get_metadata(
        client, "book.epub", valid_epub_bytes, "application/epub+zip"
    )

    assert metadata["has_cover"] is False
    assert client.get(f"/books/{metadata['id']}/cover").status_code == 404


def test_pdf_metadata_is_extracted_on_upload(client, pdf_full_metadata_bytes):
    metadata = _upload_and_get_metadata(
        client, "book.pdf", pdf_full_metadata_bytes, "application/pdf"
    )

    assert metadata["title"] == "Full Metadata PDF"
    assert metadata["title_source"] == "auto"
    assert metadata["author"] == "John Smith"
    assert metadata["author_source"] == "auto"
    assert metadata["publication_year"] == 2015
    assert metadata["needs_attention"] is False
    assert metadata["extraction_failed"] is False


def test_pdf_cover_is_extracted_from_embedded_jpeg(client, covers_dir, pdf_full_metadata_bytes):
    metadata = _upload_and_get_metadata(
        client, "book.pdf", pdf_full_metadata_bytes, "application/pdf"
    )

    assert metadata["has_cover"] is True
    cover_response = client.get(f"/books/{metadata['id']}/cover")
    assert cover_response.status_code == 200
    assert cover_response.headers["content-type"] == "image/jpeg"


def test_epub_extraction_failure_does_not_block_upload(client, epub_missing_opf_bytes):
    response = client.post(
        "/books",
        files={"files": ("broken.epub", epub_missing_opf_bytes, "application/epub+zip")},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 1
    assert body["rejected"] == []


def test_epub_extraction_failure_falls_back_to_filename_and_flags_attention(
    client, epub_missing_opf_bytes
):
    metadata = _upload_and_get_metadata(
        client, "broken.epub", epub_missing_opf_bytes, "application/epub+zip"
    )

    assert metadata["title"] == "broken.epub"
    assert metadata["title_source"] == "auto"
    assert metadata["extraction_failed"] is True
    assert metadata["needs_attention"] is True


def test_pdf_extraction_failure_does_not_block_upload_and_flags_attention(
    client, valid_pdf_bytes
):
    # valid_pdf_bytes is a minimal, non-parseable PDF (no xref table) -
    # a legitimate PDF by content signature, but pypdf cannot read it.
    metadata = _upload_and_get_metadata(client, "book.pdf", valid_pdf_bytes, "application/pdf")

    assert metadata["title"] == "book.pdf"
    assert metadata["extraction_failed"] is True
    assert metadata["needs_attention"] is True


def test_partial_epub_metadata_flags_attention_when_author_missing(client, valid_epub_bytes):
    # valid_epub_bytes has a title but no dc:creator.
    metadata = _upload_and_get_metadata(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    assert metadata["title"] == "Test Book"
    assert metadata["author"] is None
    assert metadata["extraction_failed"] is False
    assert metadata["needs_attention"] is True
