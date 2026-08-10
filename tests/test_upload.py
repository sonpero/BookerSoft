import hashlib


def test_single_file_upload_creates_one_book(client, valid_epub_bytes):
    response = client.post(
        "/books",
        files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 1
    assert body["uploaded"][0]["original_filename"] == "book.epub"
    assert body["uploaded"][0]["format"] == "epub"
    assert body["uploaded"][0]["duplicate"] is False
    assert body["rejected"] == []


def test_multiple_files_in_one_request_are_all_uploaded(client, valid_epub_bytes, valid_pdf_bytes):
    response = client.post(
        "/books",
        files=[
            ("files", ("a.epub", valid_epub_bytes, "application/epub+zip")),
            ("files", ("b.pdf", valid_pdf_bytes, "application/pdf")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["uploaded"]) == 2
    assert {b["original_filename"] for b in body["uploaded"]} == {"a.epub", "b.pdf"}


def test_renamed_jpg_is_rejected(client, fake_epub_bytes):
    response = client.post(
        "/books",
        files={"files": ("cover.epub", fake_epub_bytes, "application/epub+zip")},
    )

    body = response.json()
    assert body["uploaded"] == []
    assert len(body["rejected"]) == 1
    assert body["rejected"][0]["filename"] == "cover.epub"
    assert body["rejected"][0]["reason"]


def test_txt_file_is_rejected(client):
    response = client.post(
        "/books",
        files={"files": ("notes.txt", b"just plain text", "text/plain")},
    )

    body = response.json()
    assert body["uploaded"] == []
    assert body["rejected"][0]["filename"] == "notes.txt"


def test_batch_with_valid_and_invalid_files_are_both_reported(client, valid_epub_bytes, fake_epub_bytes):
    response = client.post(
        "/books",
        files=[
            ("files", ("good.epub", valid_epub_bytes, "application/epub+zip")),
            ("files", ("bad.epub", fake_epub_bytes, "application/epub+zip")),
        ],
    )

    body = response.json()
    assert len(body["uploaded"]) == 1
    assert body["uploaded"][0]["original_filename"] == "good.epub"
    assert len(body["rejected"]) == 1
    assert body["rejected"][0]["filename"] == "bad.epub"


def test_reuploading_same_content_is_reported_as_duplicate(client, valid_epub_bytes):
    client.post("/books", files={"files": ("first.epub", valid_epub_bytes, "application/epub+zip")})

    response = client.post(
        "/books",
        files={"files": ("first_copy.epub", valid_epub_bytes, "application/epub+zip")},
    )

    body = response.json()
    assert len(body["uploaded"]) == 1
    assert body["uploaded"][0]["duplicate"] is True
    assert client.get("/books").json().__len__() == 1


def test_stored_filename_is_derived_from_sha256_not_original_name(client, valid_epub_bytes, books_dir):
    client.post("/books", files={"files": ("My Book.epub", valid_epub_bytes, "application/epub+zip")})

    expected_sha256 = hashlib.sha256(valid_epub_bytes).hexdigest()
    assert (books_dir / f"{expected_sha256}.epub").exists()
    assert not (books_dir / "My Book.epub").exists()


def test_original_filename_with_accents_and_spaces_round_trips(client, valid_epub_bytes):
    original_name = "Été à la mer.epub"

    client.post("/books", files={"files": (original_name, valid_epub_bytes, "application/epub+zip")})

    listing = client.get("/books").json()
    assert listing[0]["original_filename"] == original_name


def test_two_books_can_share_the_same_original_filename(client, valid_epub_bytes, valid_epub_bytes_2):
    client.post("/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")})
    response = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes_2, "application/epub+zip")}
    )

    body = response.json()
    assert body["uploaded"][0]["duplicate"] is False

    listing = client.get("/books").json()
    assert len(listing) == 2
    assert all(book["original_filename"] == "book.epub" for book in listing)
    assert listing[0]["id"] != listing[1]["id"]


def test_uploaded_book_is_attributed_to_owner_user(client, db_conn, valid_epub_bytes):
    client.post("/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")})

    owner_id = db_conn.execute("SELECT id FROM users WHERE username = 'owner'").fetchone()[0]
    book_user_id = db_conn.execute("SELECT user_id FROM books").fetchone()[0]
    assert book_user_id == owner_id
