"""
API v1 dependencies - Authentication and common dependencies for API routes.
"""

import logging

from core.database import get_session
from fastapi import Depends, HTTPException, Request, status
from schemas.user import UserSession
from services import user_service
from sqlmodel import Session

logger = logging.getLogger(__name__)


def require_api_auth(
    request: Request, session: Session = Depends(get_session)
) -> UserSession:
    """
    FastAPI dependency that requires authentication for API routes.

    Unlike require_login (for template routes), this returns a JSON 401
    error instead of redirecting to /login.

    Verifies the user exists in the database (not just in the session cookie).
    If the DB was wiped but the session is still valid, re-creates the user
    from the OAuth data stored in the session.

    Args:
        request: The incoming request with session data.
        session: Database session (injected via Depends).

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
    user = UserSession.model_validate(user_data)

    # Verify user still exists in DB; re-create if DB was wiped
    db_user = user_service.get_user_by_email(session, user.email)
    if not db_user:
        logger.warning(
            "API: User %s (id=%d) not found in DB, re-creating from session",
            user.email,
            user.id,
        )
        user_session = user_service.get_or_create_user(
            session, email=user.email, name=user.name
        )
        request.session["user"] = user_session.model_dump()
        return user_session

    # If user exists but ID changed (e.g. DB recreated with different auto-increment)
    if db_user.id != user.id:
        logger.warning(
            "API: User %s ID mismatch: session=%d, db=%d. Updating session.",
            user.email,
            user.id,
            db_user.id,
        )
        user_session = UserSession(
            id=db_user.id, email=db_user.email, name=db_user.name
        )
        request.session["user"] = user_session.model_dump()
        return user_session

    return user
