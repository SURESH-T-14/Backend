from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.route import RouteResponse

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get(
    "/route",
    response_model=RouteResponse,
    summary="Get the route assigned to the authenticated user",
    description="Always returns the caller's own assigned route — there is no way to request another route's id.",
)
def read_my_route(current_user: User = Depends(get_current_user)) -> RouteResponse:
    return RouteResponse.model_validate(current_user.route)
