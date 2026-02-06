"""
API v1 dependencies - Authentication and common dependencies for API routes.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from core.database import get_session
from schemas.user import UserSession


def require_api_auth(request: Request) -> UserSession:
    """
    FastAPI dependency that requires authentication for API routes.

    Unlike require_login (for template routes), this returns a JSON 401
    error instead of redirecting to /login.

    Args:
        request: The incoming request with session data.

    Returns:
        UserSession with id, email, name.

    Raises:
        HTTPException: 401 Unauthorized if not authenticated.
    """
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserSession.model_validate(user_data)
