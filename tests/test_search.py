def _upload(client, filename, content, content_type):
    upload = client.post("/books", files={"files": (filename, content, content_type)}).json()
    return upload["uploaded"][0]["id"]


def _set_title_author(client, book_id, title=None, author=None):
    payload = {}
    if title is not None:
        payload["title"] = title
    if author is not None:
        payload["author"] = author
    client.patch(f"/books/{book_id}/metadata", json=payload)


# --- Search ---

def test_search_matches_title_case_insensitively(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="The Great Gatsby")

    results = client.get("/books", params={"q": "GREAT"}).json()

    assert [b["id"] for b in results] == [book_id]


def test_search_matches_author(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="Untitled", author="Toni Morrison")

    results = client.get("/books", params={"q": "morrison"}).json()

    assert [b["id"] for b in results] == [book_id]


def test_search_without_accents_finds_accented_title(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="Les Misérables")

    results = client.get("/books", params={"q": "miserables"}).json()

    assert [b["id"] for b in results] == [book_id]


def test_search_with_accents_finds_unaccented_title(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="Les Miserables")  # stored without accents

    results = client.get("/books", params={"q": "Misérables"}).json()

    assert [b["id"] for b in results] == [book_id]


def test_search_matches_partial_word(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="Les Misérables")

    results = client.get("/books", params={"q": "miser"}).json()

    assert [b["id"] for b in results] == [book_id]


def test_search_excludes_non_matching_books(client, valid_epub_bytes, valid_epub_bytes_2):
    match_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, match_id, title="Les Misérables")
    other_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _set_title_author(client, other_id, title="Moby Dick")

    results = client.get("/books", params={"q": "miserables"}).json()

    assert [b["id"] for b in results] == [match_id]


def test_search_with_no_match_returns_empty_list(client, valid_epub_bytes):
    book_id = _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, book_id, title="Les Misérables")

    results = client.get("/books", params={"q": "nonexistent"}).json()

    assert results == []


def test_search_query_percent_and_underscore_are_literal(client, valid_epub_bytes, valid_epub_bytes_2):
    # Special LIKE characters typed by the user must not act as wildcards.
    percent_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, percent_id, title="100% Cotton")
    other_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _set_title_author(client, other_id, title="Full Cotton")

    results = client.get("/books", params={"q": "100%"}).json()

    assert [b["id"] for b in results] == [percent_id]


# --- Filters ---

def test_filter_by_format(client, valid_epub_bytes, valid_pdf_bytes):
    _upload(client, "book.epub", valid_epub_bytes, "application/epub+zip")
    pdf_id = _upload(client, "book.pdf", valid_pdf_bytes, "application/pdf")

    results = client.get("/books", params={"format": "pdf"}).json()

    assert [b["id"] for b in results] == [pdf_id]


def test_filter_by_minimum_average_rating(client, valid_epub_bytes, valid_epub_bytes_2):
    high_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    client.put(f"/books/{high_id}/review", json={"rating": 5})
    low_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    client.put(f"/books/{low_id}/review", json={"rating": 2})

    results = client.get("/books", params={"min_rating": 4}).json()

    assert [b["id"] for b in results] == [high_id]


def test_filter_by_minimum_average_rating_excludes_unrated_books(
    client, valid_epub_bytes, valid_epub_bytes_2
):
    rated_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    client.put(f"/books/{rated_id}/review", json={"rating": 5})
    _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")  # unrated

    results = client.get("/books", params={"min_rating": 1}).json()

    assert [b["id"] for b in results] == [rated_id]


def test_filter_by_uploader(client, db_conn, valid_epub_bytes):
    _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")

    db_conn.execute("INSERT INTO users (id, username) VALUES (2, 'other_reader')")
    cursor = db_conn.execute(
        "INSERT INTO books (user_id, sha256, original_filename, stored_filename, format, size_bytes) "
        "VALUES (2, 'deadbeef', 'other.epub', 'deadbeef.epub', 'epub', 123)"
    )
    db_conn.commit()
    other_book_id = cursor.lastrowid

    results = client.get("/books", params={"uploaded_by": 2}).json()

    assert [b["id"] for b in results] == [other_book_id]


def test_needs_attention_filter_still_combines_with_search(
    client, valid_epub_bytes, epub_missing_opf_bytes
):
    ok_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, ok_id, title="Les Misérables", author="Victor Hugo")
    broken_id = _upload(client, "b.epub", epub_missing_opf_bytes, "application/epub+zip")

    results = client.get("/books", params={"needs_attention": "true"}).json()

    assert [b["id"] for b in results] == [broken_id]


def test_filters_are_combinable(client, valid_epub_bytes, valid_pdf_bytes):
    epub_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, epub_id, title="Les Misérables")
    client.put(f"/books/{epub_id}/review", json={"rating": 5})

    pdf_id = _upload(client, "b.pdf", valid_pdf_bytes, "application/pdf")
    _set_title_author(client, pdf_id, title="Les Misérables PDF edition")
    client.put(f"/books/{pdf_id}/review", json={"rating": 5})

    results = client.get(
        "/books", params={"q": "miserables", "format": "epub", "min_rating": 4}
    ).json()

    assert [b["id"] for b in results] == [epub_id]


# --- Sorting ---

def test_sort_by_title(client, valid_epub_bytes, valid_epub_bytes_2):
    z_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, z_id, title="Zebra")
    a_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _set_title_author(client, a_id, title="Apple")

    results = client.get("/books", params={"sort": "title"}).json()

    assert [b["id"] for b in results] == [a_id, z_id]


def test_sort_by_author(client, valid_epub_bytes, valid_epub_bytes_2):
    z_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    _set_title_author(client, z_id, author="Zadie Smith")
    a_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    _set_title_author(client, a_id, author="Albert Camus")

    results = client.get("/books", params={"sort": "author"}).json()

    assert [b["id"] for b in results] == [a_id, z_id]


def test_sort_by_average_rating(client, valid_epub_bytes, valid_epub_bytes_2):
    low_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    client.put(f"/books/{low_id}/review", json={"rating": 2})
    high_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")
    client.put(f"/books/{high_id}/review", json={"rating": 5})

    results = client.get("/books", params={"sort": "rating"}).json()

    assert [b["id"] for b in results] == [high_id, low_id]


def test_sort_by_average_rating_puts_unrated_books_last(client, valid_epub_bytes, valid_epub_bytes_2):
    rated_id = _upload(client, "a.epub", valid_epub_bytes, "application/epub+zip")
    client.put(f"/books/{rated_id}/review", json={"rating": 3})
    unrated_id = _upload(client, "b.epub", valid_epub_bytes_2, "application/epub+zip")

    results = client.get("/books", params={"sort": "rating"}).json()

    assert [b["id"] for b in results] == [rated_id, unrated_id]


def test_default_sort_is_recently_added(client, valid_epub_bytes, valid_pdf_bytes):
    first_id = _upload(client, "first.epub", valid_epub_bytes, "application/epub+zip")
    second_id = _upload(client, "second.pdf", valid_pdf_bytes, "application/pdf")

    results = client.get("/books").json()

    assert [b["id"] for b in results] == [second_id, first_id]


# --- Users endpoint (for the "uploaded by" filter) ---

def test_users_endpoint_lists_registered_users(client, db_conn):
    db_conn.execute("INSERT INTO users (id, username) VALUES (2, 'other_reader')")
    db_conn.commit()

    response = client.get("/users")

    assert response.status_code == 200
    usernames = {u["username"] for u in response.json()}
    assert usernames == {"owner", "other_reader"}
