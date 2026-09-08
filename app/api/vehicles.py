from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.vehicle import VehicleResponse
from app.services.tracking_service import compute_live_status, get_latest_location

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get(
    "/vehicle",
    response_model=VehicleResponse,
    summary="Get the vehicle assigned to the authenticated user",
    description="Always returns the caller's own assigned vehicle, including a server-computed live status.",
)
def read_my_vehicle(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> VehicleResponse:
    vehicle = current_user.vehicle
    latest = get_latest_location(db, vehicle.id)
    live_status = compute_live_status(latest, settings)

    return VehicleResponse(
        id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        status=vehicle.status,
        live_status=live_status,
        last_speed_kmh=latest.speed if latest else None,
        last_update=latest.timestamp if latest else None,
    )
