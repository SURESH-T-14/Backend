from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User

# auto_error=False so a missing header raises our own 401 below, instead of the
# HTTPBearer default of 403 — the spec requires 401 for any unauthenticated request.
_bearer_scheme = HTTPBearer(description="Paste the JWT returned by /api/v1/auth/login", auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the Bearer JWT, or raise 401."""
    if credentials is None:
        raise _CREDENTIALS_ERROR

    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise _CREDENTIALS_ERROR

    try:
        user_id = int(subject)
    except ValueError:
        raise _CREDENTIALS_ERROR

    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR

    return user
