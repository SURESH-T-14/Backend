from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.gps import GpsTracking
from app.models.route import Route, RoutePoint
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _fresh_database():
    """Recreate all tables before every test for full isolation."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    # Deliberately not using TestClient as a context manager: that would trigger
    # the app's lifespan and start a real MQTT connection attempt per test.
    # API requests work fine without it since no endpoint depends on startup state.
    return TestClient(app)


@pytest.fixture
def seeded_users(db_session):
    """Create User A / BUS-001 / Route A and User B / BUS-002 / Route B."""

    def _create(email: str, name: str, route_name: str, vehicle_number: str):
        route = Route(name=route_name, start_location="Start", end_location="End")
        route.points = [
            RoutePoint(sequence_index=0, latitude=13.0, longitude=80.0),
            RoutePoint(sequence_index=1, latitude=13.1, longitude=80.1),
        ]
        db_session.add(route)

        vehicle = Vehicle(vehicle_number=vehicle_number, status=VehicleStatus.ACTIVE)
        db_session.add(vehicle)
        db_session.flush()

        user = User(
            name=name,
            email=email,
            password_hash=hash_password("password123"),
            route_id=route.id,
            vehicle_id=vehicle.id,
        )
        db_session.add(user)
        db_session.flush()
        return user, route, vehicle

    user_a, route_a, vehicle_a = _create("usera@example.com", "User A", "Route A", "BUS-001")
    user_b, route_b, vehicle_b = _create("userb@example.com", "User B", "Route B", "BUS-002")
    db_session.commit()

    return {
        "user_a": user_a,
        "vehicle_a": vehicle_a,
        "route_a": route_a,
        "user_b": user_b,
        "vehicle_b": vehicle_b,
        "route_b": route_b,
    }


def add_gps_record(db_session, vehicle_id: int, lat=13.05, lon=80.05, speed=30.0, seconds_ago=0):
    record = GpsTracking(
        vehicle_id=vehicle_id,
        latitude=lat,
        longitude=lon,
        speed=speed,
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=seconds_ago),
    )
    db_session.add(record)
    db_session.commit()
    return record


def auth_headers(client, email: str, password: str = "password123") -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
