"""Simulate BUS-001 and BUS-002 moving along their real routes and publish GPS
readings over MQTT, the same way a real vehicle tracker device would.

Usage (from the backend/ directory, with the venv active and Mosquitto running):
    python scripts/gps_simulator.py
"""

import json
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from scripts.route_data import ROUTE_A_POINTS, ROUTE_B_POINTS

STEPS_PER_SEGMENT = 12  # interpolated points between each pair of real waypoints
PUBLISH_INTERVAL_RANGE = (3, 5)  # seconds
CRUISE_SPEED_RANGE_KMH = (28.0, 45.0)
STOP_PROBABILITY = 0.12  # chance a tick simulates the bus stopped at a stand


def interpolate_path(waypoints: list[tuple[float, float]], steps_per_segment: int) -> list[tuple[float, float]]:
    """Turn a sparse list of real waypoints into a dense path for smooth movement."""
    path: list[tuple[float, float]] = []
    for (lat1, lon1), (lat2, lon2) in zip(waypoints, waypoints[1:]):
        for step in range(steps_per_segment):
            t = step / steps_per_segment
            path.append((lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t))
    path.append(waypoints[-1])
    return path


@dataclass
class SimulatedVehicle:
    vehicle_id: str
    path: list[tuple[float, float]]
    index: int = 0
    direction: int = 1  # 1 = forward, -1 = backward (bounces at route ends)

    def tick(self) -> dict:
        lat, lon = self.path[self.index]

        is_stopped = random.random() < STOP_PROBABILITY
        speed = 0.0 if is_stopped else round(random.uniform(*CRUISE_SPEED_RANGE_KMH), 1)

        payload = {
            "vehicle_id": self.vehicle_id,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed": speed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not is_stopped:
            self._advance()

        return payload

    def _advance(self) -> None:
        next_index = self.index + self.direction
        if next_index < 0 or next_index >= len(self.path):
            self.direction *= -1  # reached an end of the route; turn around
            next_index = self.index + self.direction
        self.index = next_index


def build_vehicles() -> list[SimulatedVehicle]:
    return [
        SimulatedVehicle("BUS-001", interpolate_path(ROUTE_A_POINTS, STEPS_PER_SEGMENT)),
        SimulatedVehicle("BUS-002", interpolate_path(ROUTE_B_POINTS, STEPS_PER_SEGMENT)),
    ]


def main() -> None:
    settings = get_settings()
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="gps-simulator")
    client.connect(settings.mqtt_host, settings.mqtt_port)
    client.loop_start()

    vehicles = build_vehicles()
    print(f"Simulating {[v.vehicle_id for v in vehicles]} -> {settings.mqtt_host}:{settings.mqtt_port}")

    try:
        while True:
            for vehicle in vehicles:
                payload = vehicle.tick()
                topic = f"vehicles/{vehicle.vehicle_id}/location"
                client.publish(topic, json.dumps(payload), qos=1)
                print(f"Published {topic}: {payload}")
            time.sleep(random.uniform(*PUBLISH_INTERVAL_RANGE))
    except KeyboardInterrupt:
        print("Stopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
