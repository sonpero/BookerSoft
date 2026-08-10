def test_delete_removes_book_from_list(client, valid_epub_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
    assert client.get("/books").json() == []


def test_delete_removes_file_from_disk(client, valid_epub_bytes, books_dir):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    assert len(list(books_dir.iterdir())) == 1

    client.delete(f"/books/{book_id}")

    assert list(books_dir.iterdir()) == []


def test_delete_with_missing_file_on_disk_still_succeeds(client, valid_epub_bytes, books_dir):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    for stored_file in books_dir.iterdir():
        stored_file.unlink()

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
    assert client.get("/books").json() == []


def test_delete_unknown_book_returns_404(client):
    response = client.delete("/books/999999")

    assert response.status_code == 404


def test_delete_is_permanent_and_reupload_creates_a_new_row(client, valid_epub_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    client.delete(f"/books/{book_id}")

    reupload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()

    assert reupload["uploaded"][0]["duplicate"] is False
    assert reupload["uploaded"][0]["id"] != book_id
