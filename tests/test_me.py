from tests.conftest import auth_headers


def test_read_current_user(client, seeded_users):
    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "usera@example.com"
    assert body["name"] == "User A"
    assert "password" not in body
    assert "password_hash" not in body


def test_read_my_route_returns_assigned_route(client, seeded_users):
    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/route", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Route A"
    assert len(body["points"]) == 2


def test_read_my_vehicle_returns_assigned_vehicle(client, seeded_users):
    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["vehicle_number"] == "BUS-001"
    assert body["live_status"] == "offline"  # no GPS data yet
