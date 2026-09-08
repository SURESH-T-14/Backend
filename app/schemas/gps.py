from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GpsLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float
    longitude: float
    speed: float
    timestamp: datetime


class GpsIngestPayload(BaseModel):
    """Shape of the JSON payload published by the GPS simulator over MQTT."""

    vehicle_id: str = Field(min_length=1, description="Vehicle number, e.g. BUS-001")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float = Field(ge=0)
    timestamp: datetime
