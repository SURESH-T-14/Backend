"""Seed the database with two demo users, each with their own route and vehicle.

Usage (from the backend/ directory, with the venv active):
    python scripts/seed.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.route import Route, RoutePoint
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from scripts.route_data import SEED_USERS


def seed() -> None:
    db = SessionLocal()
    try:
        for spec in SEED_USERS:
            existing = db.query(User).filter(User.email == spec["email"]).first()
            if existing:
                print(f"Skipping {spec['email']} (already seeded)")
                continue

            route = Route(
                name=spec["route_name"],
                start_location=spec["route_start"],
                end_location=spec["route_end"],
            )
            route.points = [
                RoutePoint(sequence_index=i, latitude=lat, longitude=lon)
                for i, (lat, lon) in enumerate(spec["route_points"])
            ]
            db.add(route)

            vehicle = Vehicle(vehicle_number=spec["vehicle_number"], status=VehicleStatus.ACTIVE)
            db.add(vehicle)
            db.flush()  # assign route.id / vehicle.id

            user = User(
                name=spec["name"],
                email=spec["email"],
                password_hash=hash_password(spec["password"]),
                route_id=route.id,
                vehicle_id=vehicle.id,
            )
            db.add(user)
            print(f"Seeded {spec['email']} -> {spec['route_name']} / {spec['vehicle_number']}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
