EMAIL = "auth-test@katecam.dev"
PASSWORD = "password123"


def _signup(client, email=EMAIL, password=PASSWORD, nick_name="tester"):
    return client.post(
        "/auth/signup",
        json={"email": email, "password": password, "nick_name": nick_name},
    )


# Email verification is disabled for MVP (see auth.py) — new accounts are
# auto-verified on signup, so _signup_and_verify is now just _signup. Kept
# under this name so the many call sites below don't need touching if the
# feature comes back.
#
# def _verify(client, user_id: str):
#     token = create_email_verification_token(uuid.UUID(user_id))
#     return client.get("/auth/verify", params={"token": token})
def _signup_and_verify(client, email=EMAIL, password=PASSWORD):
    signup_resp = _signup(client, email, password)
    return signup_resp.json()


def test_signup_creates_verified_user(client):
    resp = _signup(client)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == EMAIL
    assert body["is_verified"] is True
    assert body["permission"] == "student"


def test_signup_duplicate_email_rejected(client):
    _signup(client)
    resp = _signup(client)

    assert resp.status_code == 400


def test_signup_short_password_rejected(client):
    resp = _signup(client, password="short")

    assert resp.status_code == 422


def test_signup_invalid_email_rejected(client):
    resp = _signup(client, email="not-an-email")

    assert resp.status_code == 422


# def test_verify_marks_user_verified(client):
#     signup_resp = _signup(client)
#     resp = _verify(client, signup_resp.json()["user_id"])
#
#     assert resp.status_code == 200
#     assert resp.json()["is_verified"] is True
#
#
# def test_verify_is_idempotent(client):
#     signup_resp = _signup(client)
#     user_id = signup_resp.json()["user_id"]
#     _verify(client, user_id)
#     resp = _verify(client, user_id)
#
#     assert resp.status_code == 200
#     assert resp.json()["is_verified"] is True
#
#
# def test_verify_invalid_token_rejected(client):
#     resp = client.get("/auth/verify", params={"token": "garbage"})
#
#     assert resp.status_code == 400
#
#
# def test_verify_unknown_user_returns_404(client):
#     token = create_email_verification_token(uuid.uuid4())
#     resp = client.get("/auth/verify", params={"token": token})
#
#     assert resp.status_code == 404
#
#
# def test_login_unverified_user_rejected(client):
#     _signup(client)
#     resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
#
#     assert resp.status_code == 403


def test_login_wrong_password_rejected(client):
    _signup_and_verify(client)
    resp = client.post("/auth/login", json={"email": EMAIL, "password": "wrong-password"})

    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post("/auth/login", json={"email": "nobody@katecam.dev", "password": PASSWORD})

    assert resp.status_code == 401


def test_login_success_returns_access_token_and_refresh_cookie(client):
    _signup_and_verify(client)
    resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})

    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.cookies


def test_refresh_without_cookie_rejected(client):
    resp = client.post("/auth/refresh")

    assert resp.status_code == 401


def test_refresh_with_garbage_cookie_rejected(client):
    client.cookies.set("refresh_token", "garbage")
    resp = client.post("/auth/refresh")

    assert resp.status_code == 401


def test_refresh_rotates_tokens(client):
    _signup_and_verify(client)
    login_resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    old_refresh_cookie = login_resp.cookies["refresh_token"]

    resp = client.post("/auth/refresh")

    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.cookies["refresh_token"] != old_refresh_cookie


def test_logout_clears_refresh_cookie(client):
    _signup_and_verify(client)
    client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})

    resp = client.post("/auth/logout")

    assert resp.status_code == 204
    refresh_resp = client.post("/auth/refresh")
    assert refresh_resp.status_code == 401


def test_users_me_requires_auth(client):
    resp = client.get("/users/me")

    assert resp.status_code == 401


def test_users_me_rejects_garbage_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer garbage"})

    assert resp.status_code == 401


def test_users_me_returns_current_user(client):
    _signup_and_verify(client)
    login_resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    access_token = login_resp.json()["access_token"]

    resp = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})

    assert resp.status_code == 200
    assert resp.json()["email"] == EMAIL
