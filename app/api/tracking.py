from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.gps import GpsLocationResponse
from app.services.tracking_service import get_history, get_latest_location

router = APIRouter(prefix="/api/v1/me", tags=["tracking"])


@router.get(
    "/vehicle/location",
    response_model=GpsLocationResponse,
    summary="Get the latest known GPS location of the authenticated user's vehicle",
)
def read_my_vehicle_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GpsLocationResponse:
    latest = get_latest_location(db, current_user.vehicle_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GPS data has been received yet for this vehicle",
        )
    return GpsLocationResponse.model_validate(latest)


@router.get(
    "/vehicle/history",
    response_model=list[GpsLocationResponse],
    summary="Get historical GPS records for the authenticated user's vehicle",
)
def read_my_vehicle_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> list[GpsLocationResponse]:
    records = get_history(db, current_user.vehicle_id, limit=limit, from_ts=from_ts, to_ts=to_ts)
    return [GpsLocationResponse.model_validate(r) for r in records]
