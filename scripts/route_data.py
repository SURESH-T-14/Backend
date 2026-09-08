"""Shared route/vehicle fixtures used by both scripts/seed.py and scripts/gps_simulator.py.

Coordinates are real waypoints along actual Chennai roads (not random points),
so the simulated buses move along a believable path rather than teleporting.
"""

ROUTE_A_POINTS = [
    (13.0827, 80.2707),  # Chennai Central
    (13.0732, 80.2609),
    (13.0569, 80.2425),
    (13.0369, 80.2205),
    (13.0210, 80.2200),
    (13.0067, 80.2206),  # Guindy
]

ROUTE_B_POINTS = [
    (12.9249, 80.1000),  # Tambaram
    (12.9165, 80.1279),
    (12.9010, 80.1620),
    (12.8994, 80.2000),
    (12.9010, 80.2279),
    (12.9010, 80.2350),  # Sholinganallur
]

SEED_USERS = [
    {
        "name": "User A",
        "email": "usera@example.com",
        "password": "password123",
        "route_name": "Route A",
        "route_start": "Chennai Central",
        "route_end": "Guindy",
        "route_points": ROUTE_A_POINTS,
        "vehicle_number": "BUS-001",
    },
    {
        "name": "User B",
        "email": "userb@example.com",
        "password": "password123",
        "route_name": "Route B",
        "route_start": "Tambaram",
        "route_end": "Sholinganallur",
        "route_points": ROUTE_B_POINTS,
        "vehicle_number": "BUS-002",
    },
]
