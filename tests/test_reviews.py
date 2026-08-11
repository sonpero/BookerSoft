def _upload(client, filename, content, content_type):
    upload = client.post("/books", files={"files": (filename, content, content_type)}).json()
    return upload["uploaded"][0]["id"]


def _upload_epub(client, valid_epub_bytes, filename="book.epub"):
    return _upload(client, filename, valid_epub_bytes, "application/epub+zip")


def test_can_set_rating_and_review(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    response = client.put(f"/books/{book_id}/review", json={"rating": 4, "review_text": "Great book"})

    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 4
    assert body["review_text"] == "Great book"
    assert body["username"] == "owner"


def test_rating_without_review_text_is_allowed(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    response = client.put(f"/books/{book_id}/review", json={"rating": 5})

    assert response.status_code == 200
    assert response.json()["review_text"] is None


def test_review_without_rating_is_rejected(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    response = client.put(f"/books/{book_id}/review", json={"review_text": "Text only, no rating"})

    assert response.status_code == 422


def test_rating_out_of_range_is_rejected(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    assert client.put(f"/books/{book_id}/review", json={"rating": 0}).status_code == 422
    assert client.put(f"/books/{book_id}/review", json={"rating": 6}).status_code == 422


def test_put_review_unknown_book_returns_404(client):
    response = client.put("/books/999999/review", json={"rating": 3})
    assert response.status_code == 404


def test_saving_again_updates_the_existing_review_instead_of_creating_a_second_row(
    client, db_conn, valid_epub_bytes
):
    book_id = _upload_epub(client, valid_epub_bytes)

    client.put(f"/books/{book_id}/review", json={"rating": 2, "review_text": "First impression"})
    response = client.put(f"/books/{book_id}/review", json={"rating": 5, "review_text": "Changed my mind"})

    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 5
    assert body["review_text"] == "Changed my mind"

    count = db_conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE book_id = ?", (book_id,)
    ).fetchone()[0]
    assert count == 1


def test_updating_a_review_changes_updated_at_but_not_created_at(client, db_conn, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 3})

    # Pin both timestamps to a known past value so the second write's effect
    # on each column can be checked deterministically, without depending on
    # wall-clock resolution between two fast successive requests.
    db_conn.execute(
        "UPDATE reviews SET created_at = '2020-01-01T00:00:00.000000Z', "
        "updated_at = '2020-01-01T00:00:00.000000Z' WHERE book_id = ?",
        (book_id,),
    )
    db_conn.commit()

    client.put(f"/books/{book_id}/review", json={"rating": 4})

    row = db_conn.execute(
        "SELECT created_at, updated_at FROM reviews WHERE book_id = ?", (book_id,)
    ).fetchone()
    assert row["created_at"] == "2020-01-01T00:00:00.000000Z"
    assert row["updated_at"] != "2020-01-01T00:00:00.000000Z"


def test_get_own_review_returns_404_when_none_exists(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    assert client.get(f"/books/{book_id}/review").status_code == 404


def test_get_own_review_returns_it_after_saving(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 3, "review_text": "Decent"})

    response = client.get(f"/books/{book_id}/review")

    assert response.status_code == 200
    assert response.json()["rating"] == 3


def test_can_delete_own_review(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 3})

    response = client.delete(f"/books/{book_id}/review")

    assert response.status_code == 204
    assert client.get(f"/books/{book_id}/review").status_code == 404
    assert client.get(f"/books/{book_id}/reviews").json() == []


def test_delete_review_when_none_exists_returns_404(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    assert client.delete(f"/books/{book_id}/review").status_code == 404


def test_reviews_list_shows_author_and_date(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 4, "review_text": "Nice"})

    reviews = client.get(f"/books/{book_id}/reviews").json()

    assert len(reviews) == 1
    assert reviews[0]["username"] == "owner"
    assert reviews[0]["rating"] == 4
    assert reviews[0]["review_text"] == "Nice"
    assert reviews[0]["updated_at"]


def test_reviews_list_unknown_book_returns_404(client):
    assert client.get("/books/999999/reviews").status_code == 404


def test_average_rating_and_count_combine_every_reviewer(client, db_conn, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    # A second reviewer, seeded directly since there is no login yet.
    db_conn.execute("INSERT INTO users (id, username) VALUES (2, 'other_reader')")
    db_conn.execute(
        "INSERT INTO reviews (book_id, user_id, rating, review_text) VALUES (?, 2, 5, 'Loved it')",
        (book_id,),
    )
    db_conn.commit()
    client.put(f"/books/{book_id}/review", json={"rating": 3})

    reviews = client.get(f"/books/{book_id}/reviews").json()
    assert len(reviews) == 2
    assert {r["username"] for r in reviews} == {"owner", "other_reader"}

    metadata = client.get(f"/books/{book_id}/metadata").json()
    assert metadata["average_rating"] == 4.0
    assert metadata["rating_count"] == 2


def test_book_with_no_reviews_has_no_average_rating(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)

    metadata = client.get(f"/books/{book_id}/metadata").json()

    assert metadata["average_rating"] is None
    assert metadata["rating_count"] == 0


def test_book_list_shows_average_rating(client, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 4})

    listing = client.get("/books").json()

    assert listing[0]["average_rating"] == 4.0
    assert listing[0]["rating_count"] == 1


def test_deleting_a_book_deletes_its_reviews(client, db_conn, valid_epub_bytes):
    book_id = _upload_epub(client, valid_epub_bytes)
    client.put(f"/books/{book_id}/review", json={"rating": 4, "review_text": "Before deletion"})

    client.delete(f"/books/{book_id}")

    count = db_conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE book_id = ?", (book_id,)
    ).fetchone()[0]
    assert count == 0
