def _upload(client, filename, content, content_type):
    upload = client.post("/books", files={"files": (filename, content, content_type)}).json()
    return upload["uploaded"][0]["id"]


def test_patch_updates_field_and_marks_source_manual(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    response = client.patch(f"/books/{book_id}/metadata", json={"author": "Manually Set Author"})

    assert response.status_code == 200
    metadata = response.json()
    assert metadata["author"] == "Manually Set Author"
    assert metadata["author_source"] == "manual"


def test_patch_only_touches_provided_fields(client, epub_full_metadata_bytes):
    book_id = _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")

    metadata = client.patch(f"/books/{book_id}/metadata", json={"title": "New Title"}).json()

    assert metadata["title"] == "New Title"
    assert metadata["title_source"] == "manual"
    # untouched fields keep their extracted value and 'auto' source
    assert metadata["author"] == "Jane Doe"
    assert metadata["author_source"] == "auto"


def test_patch_can_clear_a_field_with_explicit_null(client, epub_full_metadata_bytes):
    book_id = _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")

    metadata = client.patch(f"/books/{book_id}/metadata", json={"publisher": None}).json()

    assert metadata["publisher"] is None
    assert metadata["publisher_source"] == "manual"


def test_patch_stores_value_as_is_without_reformatting(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    metadata = client.patch(
        f"/books/{book_id}/metadata", json={"author": "  jane DOE  "}
    ).json()

    assert metadata["author"] == "  jane DOE  "


def test_patch_unknown_book_returns_404(client):
    response = client.patch("/books/999999/metadata", json={"title": "X"})
    assert response.status_code == 404


def test_reextract_refreshes_auto_fields(client, valid_epub_bytes, epub_full_metadata_bytes):
    # upload the metadata-poor file first, then swap the file on disk for one with
    # richer metadata under the same stored path is unrealistic; instead we verify
    # that a field which was never touched manually still reflects extraction after
    # an explicit re-extract call (idempotent on unchanged source content).
    book_id = _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")

    response = client.post(f"/books/{book_id}/re-extract")

    assert response.status_code == 200
    metadata = response.json()
    assert metadata["title"] == "Full Metadata Book"
    assert metadata["title_source"] == "auto"


def test_reextract_never_overwrites_a_manually_set_field(client, epub_full_metadata_bytes):
    book_id = _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")
    client.patch(f"/books/{book_id}/metadata", json={"author": "Manually Set Author"})

    metadata = client.post(f"/books/{book_id}/re-extract").json()

    assert metadata["author"] == "Manually Set Author"
    assert metadata["author_source"] == "manual"
    # a field left untouched is still refreshed by the auto extraction
    assert metadata["title"] == "Full Metadata Book"
    assert metadata["title_source"] == "auto"


def test_reextract_unknown_book_returns_404(client):
    assert client.post("/books/999999/re-extract").status_code == 404


def test_reextract_is_never_triggered_by_reuploading_a_known_file(client, epub_full_metadata_bytes):
    book_id = _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")
    client.patch(f"/books/{book_id}/metadata", json={"title": "My Custom Title"})

    # re-uploading the exact same content is reported as a duplicate (milestone 1
    # behaviour) and must never implicitly trigger a re-extraction.
    response = client.post(
        "/books", files={"files": ("book_copy.epub", epub_full_metadata_bytes, "application/epub+zip")}
    ).json()
    assert response["uploaded"][0]["duplicate"] is True

    metadata = client.get(f"/books/{book_id}/metadata").json()
    assert metadata["title"] == "My Custom Title"
    assert metadata["title_source"] == "manual"


def test_search_text_is_written_on_insert(client, db_conn, epub_full_metadata_bytes):
    _upload(client, "book.epub", epub_full_metadata_bytes, "application/epub+zip")

    search_text = db_conn.execute("SELECT search_text FROM books").fetchone()[0]
    assert "full metadata book" in search_text
    assert "jane doe" in search_text


def test_search_text_is_normalized_and_updated_on_manual_edit(client, db_conn, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    client.patch(f"/books/{book_id}/metadata", json={"title": "Les Misérables"})

    search_text = db_conn.execute(
        "SELECT search_text FROM books WHERE id = ?", (book_id,)
    ).fetchone()[0]
    assert "les miserables" in search_text
