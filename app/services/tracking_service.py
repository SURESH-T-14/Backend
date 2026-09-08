from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.gps import GpsTracking
from app.schemas.vehicle import LiveStatus


def get_latest_location(db: Session, vehicle_id: int) -> GpsTracking | None:
    stmt = (
        select(GpsTracking)
        .where(GpsTracking.vehicle_id == vehicle_id)
        .order_by(GpsTracking.timestamp.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_history(
    db: Session,
    vehicle_id: int,
    limit: int = 100,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> list[GpsTracking]:
    stmt = select(GpsTracking).where(GpsTracking.vehicle_id == vehicle_id)
    if from_ts is not None:
        stmt = stmt.where(GpsTracking.timestamp >= from_ts)
    if to_ts is not None:
        stmt = stmt.where(GpsTracking.timestamp <= to_ts)
    stmt = stmt.order_by(GpsTracking.timestamp.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


def compute_live_status(latest: GpsTracking | None, settings: Settings) -> LiveStatus:
    """Derive a real-time status purely from GPS history so all clients agree.

    OFFLINE: no reading yet, or the last reading is older than the configured threshold.
    MOVING: recent reading with speed above the moving threshold.
    STOPPED: recent reading with speed at/below the moving threshold.
    """
    if latest is None:
        return LiveStatus.OFFLINE

    # All timestamps are stored as UTC; some backends (e.g. SQLite, used in tests)
    # drop tzinfo on round-trip, so normalize before comparing.
    timestamp = latest.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
    if age_seconds > settings.vehicle_offline_after_seconds:
        return LiveStatus.OFFLINE

    if latest.speed > settings.vehicle_moving_speed_threshold_kmh:
        return LiveStatus.MOVING

    return LiveStatus.STOPPED
