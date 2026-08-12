from bookersoft.auth import MAX_LOGIN_ATTEMPTS


def _upload(client, filename, content, content_type):
    upload = client.post("/books", files={"files": (filename, content, content_type)}).json()
    return upload["uploaded"][0]["id"]


# --- Login ---

def test_login_with_correct_credentials_sets_session_and_redirects_home(auth_client, create_user):
    create_user("alice", "correct-password")

    response = auth_client.post(
        "/login", data={"username": "alice", "password": "correct-password"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session" in response.cookies

    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "secure" in set_cookie
    assert "samesite=lax" in set_cookie

    authenticated = auth_client.get("/books")
    assert authenticated.status_code == 200


def test_login_with_wrong_password_fails_without_setting_a_cookie(auth_client, create_user):
    create_user("alice", "correct-password")

    response = auth_client.post(
        "/login", data={"username": "alice", "password": "wrong-password"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"
    assert "session" not in response.cookies


def test_login_with_unknown_username_fails_the_same_way_as_wrong_password(auth_client):
    response = auth_client.post(
        "/login", data={"username": "ghost", "password": "anything"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"


def test_login_for_a_user_without_a_password_set_fails(auth_client, db_conn):
    # e.g. the seeded owner row right after a migration, before the CLI has set a password.
    db_conn.execute("INSERT INTO users (username) VALUES ('nopass')")
    db_conn.commit()

    response = auth_client.post(
        "/login", data={"username": "nopass", "password": "anything"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"


# --- Rate limiting ---

def test_repeated_failed_logins_from_the_same_client_are_rate_limited(auth_client, create_user):
    create_user("alice", "correct-password")

    for _ in range(MAX_LOGIN_ATTEMPTS):
        auth_client.post(
            "/login", data={"username": "alice", "password": "wrong"}, follow_redirects=False
        )

    response = auth_client.post(
        "/login", data={"username": "alice", "password": "correct-password"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=rate_limited"
    assert "session" not in response.cookies


def test_successful_login_resets_the_failed_attempt_counter(auth_client, create_user):
    create_user("alice", "correct-password")
    auth_client.post("/login", data={"username": "alice", "password": "wrong"}, follow_redirects=False)

    response = auth_client.post(
        "/login", data={"username": "alice", "password": "correct-password"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"


# --- Session-gated pages and API ---

def test_home_page_without_session_redirects_to_login(auth_client):
    response = auth_client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_book_detail_page_without_session_redirects_to_login(auth_client):
    response = auth_client.get("/books/1", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_page_itself_is_reachable_without_a_session(auth_client):
    response = auth_client.get("/login")

    assert response.status_code == 200


def test_api_call_without_session_returns_401(auth_client):
    response = auth_client.get("/books")

    assert response.status_code == 401


def test_home_page_with_valid_session_serves_the_app(auth_client, create_user, login):
    create_user("alice", "correct-password")
    login("alice", "correct-password")

    response = auth_client.get("/", follow_redirects=False)

    assert response.status_code == 200


def test_logout_clears_the_session(auth_client, create_user, login):
    create_user("alice", "correct-password")
    login("alice", "correct-password")
    assert auth_client.get("/books").status_code == 200

    auth_client.post("/logout", follow_redirects=False)

    assert auth_client.get("/books").status_code == 401


# --- A user can't touch another user's review ---

def test_user_cannot_modify_another_users_review(auth_client, create_user, login, valid_epub_bytes):
    create_user("alice", "alice-password")
    create_user("bob", "bob-password")

    login("alice", "alice-password")
    book_id = _upload(auth_client, "book.epub", valid_epub_bytes, "application/epub+zip")
    auth_client.put(f"/books/{book_id}/review", json={"rating": 5, "review_text": "Alice's take"})

    login("bob", "bob-password")
    auth_client.put(f"/books/{book_id}/review", json={"rating": 2, "review_text": "Bob's take"})

    reviews = {r["username"]: r for r in auth_client.get(f"/books/{book_id}/reviews").json()}
    assert reviews["alice"]["rating"] == 5
    assert reviews["alice"]["review_text"] == "Alice's take"
    assert reviews["bob"]["rating"] == 2


def test_user_cannot_delete_another_users_review(auth_client, create_user, login, valid_epub_bytes):
    create_user("alice", "alice-password")
    create_user("bob", "bob-password")

    login("alice", "alice-password")
    book_id = _upload(auth_client, "book.epub", valid_epub_bytes, "application/epub+zip")
    auth_client.put(f"/books/{book_id}/review", json={"rating": 4})

    login("bob", "bob-password")
    response = auth_client.delete(f"/books/{book_id}/review")

    assert response.status_code == 404  # bob has no review of his own to delete
    reviews = auth_client.get(f"/books/{book_id}/reviews").json()
    assert len(reviews) == 1
    assert reviews[0]["username"] == "alice"


# --- Only the uploader and the owner can delete a book ---

def test_uploader_can_delete_their_own_book(auth_client, create_user, login, valid_epub_bytes):
    create_user("alice", "alice-password")
    login("alice", "alice-password")
    book_id = _upload(auth_client, "book.epub", valid_epub_bytes, "application/epub+zip")

    response = auth_client.delete(f"/books/{book_id}")

    assert response.status_code == 204


def test_owner_can_delete_a_book_uploaded_by_someone_else(
    auth_client, create_user, login, valid_epub_bytes
):
    create_user("alice", "alice-password")
    create_user("owner", "owner-password", is_owner=True)

    login("alice", "alice-password")
    book_id = _upload(auth_client, "book.epub", valid_epub_bytes, "application/epub+zip")

    login("owner", "owner-password")
    response = auth_client.delete(f"/books/{book_id}")

    assert response.status_code == 204


def test_non_owner_cannot_delete_a_book_uploaded_by_someone_else(
    auth_client, create_user, login, valid_epub_bytes
):
    create_user("alice", "alice-password")
    create_user("bob", "bob-password")

    login("alice", "alice-password")
    book_id = _upload(auth_client, "book.epub", valid_epub_bytes, "application/epub+zip")

    login("bob", "bob-password")
    response = auth_client.delete(f"/books/{book_id}")

    assert response.status_code == 403
    assert auth_client.get(f"/books/{book_id}/metadata").status_code == 200
