import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.vehicle import VehicleStatus


class LiveStatus(str, enum.Enum):
    """GPS-derived, real-time status shown to the client (distinct from VehicleStatus)."""

    MOVING = "moving"
    STOPPED = "stopped"
    OFFLINE = "offline"


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_number: str
    status: VehicleStatus
    live_status: LiveStatus
    last_speed_kmh: float | None
    last_update: datetime | None
