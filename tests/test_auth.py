def test_login_success(client, seeded_users):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 0


def test_login_wrong_password_fails(client, seeded_users):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_unknown_email_fails(client, seeded_users):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_without_token_returns_401(client, seeded_users):
    resp = client.get("/api/v1/me")
    assert resp.status_code == 401


def test_protected_endpoint_with_garbage_token_returns_401(client, seeded_users):
    resp = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
