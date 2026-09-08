from sqlalchemy.orm import Session

from app.models.gps import GpsTracking
from app.schemas.gps import GpsIngestPayload


def store_gps_reading(db: Session, vehicle_id: int, payload: GpsIngestPayload) -> GpsTracking:
    """Persist a validated GPS reading. Caller is responsible for commit/rollback."""
    record = GpsTracking(
        vehicle_id=vehicle_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        timestamp=payload.timestamp,
    )
    db.add(record)
    db.flush()
    return record
