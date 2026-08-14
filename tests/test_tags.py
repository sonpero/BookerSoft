def _upload(client, filename, content, content_type):
    upload = client.post("/books", files={"files": (filename, content, content_type)}).json()
    return upload["uploaded"][0]["id"]


def _add_tag(client, book_id, name):
    return client.post(f"/books/{book_id}/tags", json={"name": name})


def _tag_names(tags):
    return {t["name"] for t in tags}


# --- Normalization ---


def test_tag_name_is_trimmed_lowercased_and_whitespace_collapsed(
    client, valid_epub_bytes, valid_epub_bytes_2
):
    book_a = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    book_b = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")

    _add_tag(client, book_a, "  Tech   Guide  ")
    _add_tag(client, book_b, "tech guide")

    tags = client.get("/tags").json()

    assert len(tags) == 1
    assert tags[0]["name"] == "tech guide"
    assert tags[0]["book_count"] == 2


# --- Editing ---


def test_add_tag_appears_on_book_detail_and_list(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    _add_tag(client, book_id, "fiction")

    detail = client.get(f"/books/{book_id}/metadata").json()
    assert _tag_names(detail["tags"]) == {"fiction"}

    [summary] = client.get("/books").json()
    assert _tag_names(summary["tags"]) == {"fiction"}


def test_add_tag_response_status_is_success(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    response = _add_tag(client, book_id, "fiction")

    assert response.status_code == 200


def test_adding_duplicate_tag_is_a_noop_without_error(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _add_tag(client, book_id, "fiction")

    response = _add_tag(client, book_id, "fiction")

    assert response.status_code == 200
    detail = client.get(f"/books/{book_id}/metadata").json()
    assert len(detail["tags"]) == 1


def test_remove_tag_from_book(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    tag = _add_tag(client, book_id, "fiction").json()[0]

    response = client.delete(f"/books/{book_id}/tags/{tag['id']}")

    assert response.status_code == 204
    detail = client.get(f"/books/{book_id}/metadata").json()
    assert detail["tags"] == []


def test_add_tag_to_unknown_book_returns_404(client):
    response = _add_tag(client, 999999, "fiction")

    assert response.status_code == 404


def test_remove_tag_from_unknown_book_returns_404(client):
    response = client.delete("/books/999999/tags/1")

    assert response.status_code == 404


def test_removing_a_tag_not_on_the_book_is_idempotent(client, valid_epub_bytes, valid_epub_bytes_2):
    # Consistent with adding a tag already present: no error either way.
    book_a = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    book_b = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    tag = _add_tag(client, book_b, "fiction").json()[0]  # tag exists, but not on book_a

    response = client.delete(f"/books/{book_a}/tags/{tag['id']}")

    assert response.status_code == 204
    # And it didn't touch book_b's association either.
    detail = client.get(f"/books/{book_b}/metadata").json()
    assert _tag_names(detail["tags"]) == {"fiction"}


def test_adding_empty_tag_name_is_rejected(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    response = _add_tag(client, book_id, "   ")

    assert response.status_code == 400
    detail = client.get(f"/books/{book_id}/metadata").json()
    assert detail["tags"] == []


# --- Orphaned tag cleanup ---


def test_removing_last_association_deletes_the_orphaned_tag(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    tag = _add_tag(client, book_id, "fiction").json()[0]

    client.delete(f"/books/{book_id}/tags/{tag['id']}")

    assert client.get("/tags").json() == []


def test_removing_association_keeps_tag_still_used_elsewhere(
    client, valid_epub_bytes, valid_epub_bytes_2
):
    book_a = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    book_b = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    tag = _add_tag(client, book_a, "fiction").json()[0]
    _add_tag(client, book_b, "fiction")

    client.delete(f"/books/{book_a}/tags/{tag['id']}")

    tags = client.get("/tags").json()
    assert len(tags) == 1
    assert tags[0]["book_count"] == 1


def test_deleting_a_book_removes_its_now_orphaned_tags(client, db_conn, valid_epub_bytes):
    # The cascade delete on book_tags (ON DELETE CASCADE from books) is what's
    # supposed to fire the orphaned-tag trigger — this only actually happens
    # if PRAGMA foreign_keys is on for the connection, so this test exercises
    # that, not just the app-level "remove one tag" path above.
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _add_tag(client, book_id, "fiction")

    client.delete(f"/books/{book_id}")

    assert client.get("/tags").json() == []
    assert db_conn.execute("SELECT * FROM tags").fetchall() == []
    assert db_conn.execute("SELECT * FROM book_tags").fetchall() == []


def test_deleting_a_book_does_not_remove_a_tag_still_used_by_another_book(
    client, valid_epub_bytes, valid_epub_bytes_2
):
    book_a = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    book_b = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _add_tag(client, book_a, "fiction")
    _add_tag(client, book_b, "fiction")

    client.delete(f"/books/{book_a}")

    tags = client.get("/tags").json()
    assert len(tags) == 1
    assert tags[0]["name"] == "fiction"
    assert tags[0]["book_count"] == 1


# --- Filtering ---


def test_filter_by_a_single_tag(client, valid_epub_bytes, valid_epub_bytes_2):
    tagged_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    tag = _add_tag(client, tagged_id, "fiction").json()[0]
    _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")  # untagged

    results = client.get("/books", params={"tags": [tag["id"]]}).json()

    assert [b["id"] for b in results] == [tagged_id]


def test_filter_by_multiple_tags_requires_all_of_them(
    client, valid_epub_bytes, valid_epub_bytes_2, valid_pdf_bytes
):
    fiction_only = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    fiction_tag = _add_tag(client, fiction_only, "fiction").json()[0]

    classic_only = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    classic_tag = _add_tag(client, classic_only, "classic").json()[0]

    both = _upload(client, "c.pdf", valid_pdf_bytes, "application/pdf")
    _add_tag(client, both, "fiction")
    _add_tag(client, both, "classic")

    results = client.get(
        "/books", params={"tags": [fiction_tag["id"], classic_tag["id"]]}
    ).json()

    assert [b["id"] for b in results] == [both]


def test_tag_filter_combines_with_search_and_format(
    client, valid_epub_bytes, valid_pdf_bytes
):
    match = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    client.patch(f"/books/{match}/metadata", json={"title": "Les Misérables"})
    tag = _add_tag(client, match, "classic").json()[0]

    # Same tag and title, wrong format — must be excluded once format is added.
    other_format = _upload(client, "b.pdf", valid_pdf_bytes, "application/pdf")
    client.patch(f"/books/{other_format}/metadata", json={"title": "Les Misérables PDF"})
    _add_tag(client, other_format, "classic")

    results = client.get(
        "/books",
        params={"q": "miserables", "tags": [tag["id"]], "format": "epub"},
    ).json()

    assert [b["id"] for b in results] == [match]


def test_filter_by_unknown_tag_id_returns_no_books(client, valid_epub_bytes):
    _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")

    results = client.get("/books", params={"tags": [999999]}).json()

    assert results == []


# --- Tags listing (filter bar + autocomplete) ---


def test_tags_endpoint_lists_every_tag_with_its_book_count(
    client, valid_epub_bytes, valid_epub_bytes_2
):
    book_a = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    book_b = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _add_tag(client, book_a, "fiction")
    _add_tag(client, book_b, "fiction")
    _add_tag(client, book_b, "classic")

    tags = {t["name"]: t["book_count"] for t in client.get("/tags").json()}

    assert tags == {"fiction": 2, "classic": 1}
