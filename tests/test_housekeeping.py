def test_needs_attention_filter_returns_only_flagged_books(
    client, epub_full_metadata_bytes, epub_missing_opf_bytes
):
    client.post(
        "/books", files={"files": ("good.epub", epub_full_metadata_bytes, "application/epub+zip")}
    )
    client.post(
        "/books", files={"files": ("broken.epub", epub_missing_opf_bytes, "application/epub+zip")}
    )

    listing = client.get("/books?needs_attention=true").json()

    assert len(listing) == 1
    assert listing[0]["original_filename"] == "broken.epub"
    assert listing[0]["needs_attention"] is True


def test_needs_attention_filter_off_returns_every_book(
    client, epub_full_metadata_bytes, epub_missing_opf_bytes
):
    client.post(
        "/books", files={"files": ("good.epub", epub_full_metadata_bytes, "application/epub+zip")}
    )
    client.post(
        "/books", files={"files": ("broken.epub", epub_missing_opf_bytes, "application/epub+zip")}
    )

    listing = client.get("/books").json()

    assert len(listing) == 2


def test_delete_also_deletes_cover_file(client, covers_dir, epub_full_metadata_bytes):
    upload = client.post(
        "/books", files={"files": ("book.epub", epub_full_metadata_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    assert len(list(covers_dir.iterdir())) == 1

    client.delete(f"/books/{book_id}")

    assert list(covers_dir.iterdir()) == []


def test_delete_with_missing_cover_file_on_disk_still_succeeds(
    client, covers_dir, epub_full_metadata_bytes
):
    upload = client.post(
        "/books", files={"files": ("book.epub", epub_full_metadata_bytes, "application/epub+zip")}
    ).json()
    book_id = upload["uploaded"][0]["id"]
    for cover_file in covers_dir.iterdir():
        cover_file.unlink()

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
