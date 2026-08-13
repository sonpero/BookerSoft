import urllib.parse


def test_download_returns_original_content_and_filename(client, valid_epub_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    response = client.get(f"/books/{book_id}/file")

    assert response.status_code == 200
    assert response.content == valid_epub_bytes
    assert response.headers["content-type"] == "application/epub+zip"
    assert 'filename="book.epub"' in response.headers["content-disposition"]


def test_download_pdf_has_correct_mime_type(client, valid_pdf_bytes):
    upload = client.post(
        "/books", files={"files": ("book.pdf", valid_pdf_bytes, "application/pdf")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    response = client.get(f"/books/{book_id}/file")

    assert response.headers["content-type"] == "application/pdf"


def test_download_encodes_accented_filename_per_rfc5987(client, valid_epub_bytes):
    original_name = "Été à la mer.epub"
    upload = client.post(
        "/books", files={"files": (original_name, valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    response = client.get(f"/books/{book_id}/file")

    disposition = response.headers["content-disposition"]
    assert "filename*=UTF-8''" in disposition
    assert urllib.parse.quote(original_name) in disposition


def test_download_unknown_book_returns_404(client):
    response = client.get("/books/999999/file")

    assert response.status_code == 404


def test_download_rejects_path_traversal_in_url(client):
    response = client.get("/books/../../etc/passwd/file")

    assert response.status_code == 404


def test_download_link_click_for_deleted_book_returns_json_404_not_the_app_shell(
    client, valid_epub_bytes
):
    # Same request a real <a href> click makes: the browser sends "text/html"
    # in Accept for the navigation, even though the response is meant to be
    # a file. The book existed when the page rendered the link but was
    # deleted before the click landed, so the SPA catch-all in main.py must
    # not mistake this for a page navigation and serve the shell under the
    # book's name instead of a plain 404.
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    client.delete(f"/books/{book_id}")

    response = client.get(
        f"/books/{book_id}/file",
        headers={"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
    )

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"


def test_download_is_recorded(client, db_conn, valid_epub_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", valid_epub_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]

    client.get(f"/books/{book_id}/file")

    count = db_conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE book_id = ?", (book_id,)
    ).fetchone()[0]
    assert count == 1
