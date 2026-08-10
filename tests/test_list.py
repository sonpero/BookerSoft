def test_empty_library_returns_empty_list(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json() == []


def test_list_shows_filename_size_and_upload_date(client, valid_epub_bytes):
    client.post("/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")})

    listing = client.get("/books").json()

    assert len(listing) == 1
    book = listing[0]
    assert book["original_filename"] == "book.epub"
    assert book["size_bytes"] == len(valid_epub_bytes)
    assert book["uploaded_at"]


def test_list_orders_newest_first(client, valid_epub_bytes, valid_pdf_bytes):
    client.post("/books", files={"files": ("first.epub", valid_epub_bytes, "application/epub+zip")})
    client.post("/books", files={"files": ("second.pdf", valid_pdf_bytes, "application/pdf")})

    listing = client.get("/books").json()

    assert [book["original_filename"] for book in listing] == ["second.pdf", "first.epub"]
