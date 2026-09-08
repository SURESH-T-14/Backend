import json
from datetime import datetime, timezone

import pytest

from app.models.gps import GpsTracking
from app.mqtt.subscriber import MqttSubscriber
from tests.conftest import TestingSessionLocal


class FakeMqttMessage:
    """Stand-in for paho's MQTTMessage: only .topic/.payload are read by _on_message."""

    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = payload


@pytest.fixture
def subscriber(monkeypatch):
    # The subscriber opens its own SQLAlchemy session per message via SessionLocal,
    # which is normally bound to the real Postgres engine. Point it at the same
    # SQLite engine the rest of the test suite uses.
    monkeypatch.setattr("app.mqtt.subscriber.SessionLocal", TestingSessionLocal)
    return MqttSubscriber()


def _publish(subscriber: MqttSubscriber, vehicle_number: str, body: dict) -> None:
    msg = FakeMqttMessage(f"vehicles/{vehicle_number}/location", json.dumps(body).encode("utf-8"))
    subscriber._on_message(None, None, msg)


def test_valid_payload_is_stored_for_known_vehicle(subscriber, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    _publish(
        subscriber,
        "BUS-001",
        {
            "vehicle_id": "BUS-001",
            "latitude": 13.05,
            "longitude": 80.2,
            "speed": 25.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    records = db_session.query(GpsTracking).filter(GpsTracking.vehicle_id == vehicle_a.id).all()
    assert len(records) == 1
    assert records[0].speed == 25.5
    assert records[0].latitude == 13.05


def test_unknown_vehicle_is_discarded_without_error(subscriber, db_session, seeded_users):
    _publish(
        subscriber,
        "BUS-999",
        {
            "vehicle_id": "BUS-999",
            "latitude": 13.05,
            "longitude": 80.2,
            "speed": 25.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert db_session.query(GpsTracking).count() == 0


def test_invalid_latitude_is_rejected(subscriber, db_session, seeded_users):
    _publish(
        subscriber,
        "BUS-001",
        {
            "vehicle_id": "BUS-001",
            "latitude": 999.0,
            "longitude": 80.2,
            "speed": 25.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert db_session.query(GpsTracking).count() == 0


def test_negative_speed_is_rejected(subscriber, db_session, seeded_users):
    _publish(
        subscriber,
        "BUS-001",
        {
            "vehicle_id": "BUS-001",
            "latitude": 13.05,
            "longitude": 80.2,
            "speed": -5.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert db_session.query(GpsTracking).count() == 0


def test_missing_required_field_is_rejected(subscriber, db_session, seeded_users):
    _publish(
        subscriber,
        "BUS-001",
        {
            "vehicle_id": "BUS-001",
            "latitude": 13.05,
            "longitude": 80.2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert db_session.query(GpsTracking).count() == 0


def test_malformed_json_is_discarded(subscriber, db_session, seeded_users):
    msg = FakeMqttMessage("vehicles/BUS-001/location", b"not-json{{{")
    subscriber._on_message(None, None, msg)
    assert db_session.query(GpsTracking).count() == 0


def test_reading_for_vehicle_a_never_lands_on_vehicle_b(subscriber, db_session, seeded_users):
    vehicle_a = seeded_users["vehicle_a"]
    vehicle_b = seeded_users["vehicle_b"]
    _publish(
        subscriber,
        "BUS-001",
        {
            "vehicle_id": "BUS-001",
            "latitude": 13.05,
            "longitude": 80.2,
            "speed": 25.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert db_session.query(GpsTracking).filter(GpsTracking.vehicle_id == vehicle_a.id).count() == 1
    assert db_session.query(GpsTracking).filter(GpsTracking.vehicle_id == vehicle_b.id).count() == 0
