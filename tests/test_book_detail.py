def test_detail_page_is_reachable_by_id(client, valid_epub_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_detail_endpoint_returns_full_metadata(client, epub_full_metadata_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", epub_full_metadata_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    metadata = client.get(f"/books/{book_id}/metadata").json()

    assert metadata["id"] == book_id
    assert metadata["original_filename"] == "book.epub"
    assert metadata["format"] == "epub"
    assert metadata["description"].startswith("A gripping tale of adventure.")
    for field in ("title", "author", "language", "publication_year", "publisher", "isbn", "description"):
        assert metadata[f"{field}_source"] == "auto"


def test_detail_endpoint_unknown_book_returns_404(client):
    assert client.get("/books/999999/metadata").status_code == 404


def test_detail_page_serves_shell_even_for_unknown_book(client):
    # The page itself always renders; its JS is responsible for fetching
    # /books/{id}/metadata and showing a "not found" state client-side.
    response = client.get("/books/999999")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
