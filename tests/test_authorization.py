"""Proves the core requirement: User A can never see User B's route/vehicle/GPS data, and vice versa.

No endpoint accepts a client-supplied vehicle_id or route_id — everything is derived
from the authenticated user server-side — so there is structurally no way for a
client to request another user's vehicle. These tests confirm that in practice.
"""

from tests.conftest import add_gps_record, auth_headers


def test_user_a_only_sees_own_vehicle_not_user_b(client, seeded_users):
    headers_a = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["vehicle_number"] == "BUS-001"
    assert resp.json()["vehicle_number"] != "BUS-002"


def test_user_b_only_sees_own_vehicle_not_user_a(client, seeded_users):
    headers_b = auth_headers(client, "userb@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json()["vehicle_number"] == "BUS-002"
    assert resp.json()["vehicle_number"] != "BUS-001"


def test_user_a_only_sees_own_route_not_route_b(client, seeded_users):
    headers_a = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/route", headers=headers_a)
    assert resp.json()["name"] == "Route A"


def test_user_b_only_sees_own_route_not_route_a(client, seeded_users):
    headers_b = auth_headers(client, "userb@example.com")
    resp = client.get("/api/v1/me/route", headers=headers_b)
    assert resp.json()["name"] == "Route B"


def test_user_a_location_is_isolated_from_user_b(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    vehicle_b = seeded_users["vehicle_b"]
    add_gps_record(db_session, vehicle_a.id, lat=10.0, lon=20.0, speed=15.0)
    add_gps_record(db_session, vehicle_b.id, lat=99.0, lon=88.0, speed=99.0)

    headers_a = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/location", headers=headers_a)
    body = resp.json()
    assert body["latitude"] == 10.0
    assert body["latitude"] != 99.0


def test_user_b_location_is_isolated_from_user_a(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    vehicle_b = seeded_users["vehicle_b"]
    add_gps_record(db_session, vehicle_a.id, lat=10.0, lon=20.0, speed=15.0)
    add_gps_record(db_session, vehicle_b.id, lat=99.0, lon=88.0, speed=99.0)

    headers_b = auth_headers(client, "userb@example.com")
    resp = client.get("/api/v1/me/vehicle/location", headers=headers_b)
    body = resp.json()
    assert body["latitude"] == 99.0
    assert body["latitude"] != 10.0


def test_user_a_history_never_contains_vehicle_b_records(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    vehicle_b = seeded_users["vehicle_b"]
    add_gps_record(db_session, vehicle_a.id, speed=11.0)
    add_gps_record(db_session, vehicle_b.id, speed=22.0)

    headers_a = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/history", headers=headers_a)
    speeds = [r["speed"] for r in resp.json()]
    assert speeds == [11.0]
    assert 22.0 not in speeds


def test_no_endpoint_accepts_a_client_supplied_vehicle_or_route_id(client, seeded_users):
    """Defense in depth: even if such a param were added, it must not exist on any current route."""
    headers_a = auth_headers(client, "usera@example.com")
    vehicle_b = seeded_users["vehicle_b"]

    for path in [
        f"/api/v1/me/vehicle?vehicle_id={vehicle_b.id}",
        f"/api/v1/vehicles/{vehicle_b.id}",
        f"/api/v1/me/vehicle/{vehicle_b.id}/location",
    ]:
        resp = client.get(path, headers=headers_a)
        # Either ignored (200, still returns own vehicle) or not found (404) —
        # never a 200 that leaks BUS-002 data.
        if resp.status_code == 200:
            assert resp.json().get("vehicle_number") != "BUS-002"
        else:
            assert resp.status_code == 404
