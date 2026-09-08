from tests.conftest import add_gps_record, auth_headers


def test_latest_location_returns_404_when_no_data(client, seeded_users):
    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/location", headers=headers)
    assert resp.status_code == 404


def test_latest_location_returns_most_recent_reading(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    add_gps_record(db_session, vehicle_a.id, lat=13.01, lon=80.01, speed=10.0, seconds_ago=60)
    add_gps_record(db_session, vehicle_a.id, lat=13.02, lon=80.02, speed=20.0, seconds_ago=5)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/location", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["latitude"] == 13.02
    assert body["speed"] == 20.0


def test_vehicle_status_moving_when_recent_and_fast(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    add_gps_record(db_session, vehicle_a.id, speed=40.0, seconds_ago=2)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers)
    assert resp.json()["live_status"] == "moving"


def test_vehicle_status_stopped_when_recent_and_slow(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    add_gps_record(db_session, vehicle_a.id, speed=0.0, seconds_ago=2)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers)
    assert resp.json()["live_status"] == "stopped"


def test_vehicle_status_offline_when_stale(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    add_gps_record(db_session, vehicle_a.id, speed=40.0, seconds_ago=3600)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle", headers=headers)
    assert resp.json()["live_status"] == "offline"


def test_history_returns_records_ordered_newest_first(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    add_gps_record(db_session, vehicle_a.id, speed=10.0, seconds_ago=120)
    add_gps_record(db_session, vehicle_a.id, speed=20.0, seconds_ago=60)
    add_gps_record(db_session, vehicle_a.id, speed=30.0, seconds_ago=5)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/history", headers=headers)
    assert resp.status_code == 200
    speeds = [r["speed"] for r in resp.json()]
    assert speeds == [30.0, 20.0, 10.0]


def test_history_respects_limit(client, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    for i in range(5):
        add_gps_record(db_session, vehicle_a.id, speed=float(i), seconds_ago=i)

    headers = auth_headers(client, "usera@example.com")
    resp = client.get("/api/v1/me/vehicle/history?limit=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2
