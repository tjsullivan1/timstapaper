"""
Security and authentication utilities.

Provides authentication dependencies and user session management.
Uses Google OAuth for user authentication with session-based auth.
"""

from typing import Optional

from fastapi import HTTPException, Request, status


def get_current_user(request: Request) -> Optional[dict]:
    """
    Get the current user from the session.

    Args:
        request: The incoming request with session data.

    Returns:
        User dict with id, email, name if logged in, None otherwise.
    """
    return request.session.get("user")


def require_login(request: Request) -> dict:
    """
    FastAPI dependency that requires an authenticated user.

    Use with Depends() to protect routes that require authentication.

    Args:
        request: The incoming request with session data.

    Returns:
        User dict with id, email, name.

    Raises:
        HTTPException: 303 redirect to /login if not authenticated.

    Example:
        @app.get("/dashboard")
        async def dashboard(user: dict = Depends(require_login)):
            return {"user": user}
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user
