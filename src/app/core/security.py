"""
Security and authentication utilities.

Provides authentication dependencies and user session management.
Uses Google OAuth for user authentication with session-based auth.
"""

import logging

from fastapi import Depends, HTTPException, Request, status
from schemas.user import UserSession
from services import user_service
from sqlmodel import Session

from core.database import get_session

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> UserSession | None:
    """
    Get the current user from the session.

    Args:
        request: The incoming request with session data.

    Returns:
        UserSession if logged in, None otherwise.
    """
    user_data = request.session.get("user")
    if user_data:
        return UserSession.model_validate(user_data)
    return None


def require_login(
    request: Request, session: Session = Depends(get_session)
) -> UserSession:
    """
    FastAPI dependency that requires an authenticated user.

    Verifies the user exists in the database (not just in the session cookie).
    If the DB was wiped but the session is still valid, re-creates the user
    from the OAuth data stored in the session.

    Use with Depends() to protect routes that require authentication.

    Args:
        request: The incoming request with session data.
        session: Database session (injected via Depends).

    Returns:
        UserSession with id, email, name.

    Raises:
        HTTPException: 303 redirect to /login if not authenticated.

    Example:
        @app.get("/dashboard")
        async def dashboard(user: UserSession = Depends(require_login)):
            return {"user": user}
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )

    # Verify user still exists in DB; re-create if DB was wiped
    db_user = user_service.get_user_by_email(session, user.email)
    if not db_user:
        logger.warning(
            "User %s (id=%d) not found in DB, re-creating from session",
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
            "User %s ID mismatch: session=%d, db=%d. Updating session.",
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
